/*
 * Copyright 2018 Splunk, Inc..
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package main

import (
	"bytes"
	"compress/gzip"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/daemon/logger"
	"github.com/docker/docker/daemon/logger/loggerutils"
	"github.com/docker/docker/pkg/urlutil"
)

const (
	driverName                    = "splunk"
	splunkURLKey                  = "splunk-url"
	splunkURLPathKey              = "splunk-url-path"
	splunkTokenKey                = "splunk-token"
	splunkSourceKey               = "splunk-source"
	splunkSourceTypeKey           = "splunk-sourcetype"
	splunkIndexKey                = "splunk-index"
	splunkCAPathKey               = "splunk-capath"
	splunkCANameKey               = "splunk-caname"
	splunkInsecureSkipVerifyKey   = "splunk-insecureskipverify"
	splunkFormatKey               = "splunk-format"
	splunkVerifyConnectionKey     = "splunk-verify-connection"
	splunkGzipCompressionKey      = "splunk-gzip"
	splunkGzipCompressionLevelKey = "splunk-gzip-level"
	envKey                        = "env"
	envRegexKey                   = "env-regex"
	labelsKey                     = "labels"
	tagKey                        = "tag"
)

const (
	// How often do we send messages (if we are not reaching batch size)
	defaultPostMessagesFrequency = 5 * time.Second
	// How big can be batch of messages
	defaultPostMessagesBatchSize = 1000
	// Maximum number of messages we can store in buffer
	defaultBufferMaximum = 10 * defaultPostMessagesBatchSize
	// Number of messages allowed to be queued in the channel
	defaultStreamChannelSize = 4 * defaultPostMessagesBatchSize
	// Partial log hold duration (if we are not reaching max buffer size)
	defaultPartialMsgBufferHoldDuration = 5 * time.Second
	// Maximum buffer size for partial logging
	defaultPartialMsgBufferMaximum = 1024 * 1024
	// Number of retry if error happens while reading logs from docker provided fifo
	// -1 means retry forever
	defaultReadFifoErrorRetryNumber = 3
	// Determines if JSON logging is enabled
	defaultJSONLogs = true
	// Determines if telemetry is enabled
	defaultSplunkTelemetry = true
)

const (
	envVarPostMessagesFrequency        = "SPLUNK_LOGGING_DRIVER_POST_MESSAGES_FREQUENCY"
	envVarPostMessagesBatchSize        = "SPLUNK_LOGGING_DRIVER_POST_MESSAGES_BATCH_SIZE"
	envVarBufferMaximum                = "SPLUNK_LOGGING_DRIVER_BUFFER_MAX"
	envVarStreamChannelSize            = "SPLUNK_LOGGING_DRIVER_CHANNEL_SIZE"
	envVarPartialMsgBufferHoldDuration = "SPLUNK_LOGGING_DRIVER_TEMP_MESSAGES_HOLD_DURATION"
	envVarPartialMsgBufferMaximum      = "SPLUNK_LOGGING_DRIVER_TEMP_MESSAGES_BUFFER_SIZE"
	envVarReadFifoErrorRetryNumber     = "SPLUNK_LOGGING_DRIVER_FIFO_ERROR_RETRY_TIME"
	envVarJSONLogs                     = "SPLUNK_LOGGING_DRIVER_JSON_LOGS"
	envVarSplunkTelemetry              = "SPLUNK_TELEMETRY"
)

type splunkLoggerInterface interface {
	logger.Logger
	worker()
}

type splunkLogger struct {
	hec         *hecClient
	nullMessage *splunkMessage

	// For synchronization between background worker and logger.
	// We use channel to send messages to worker go routine.
	// All other variables for blocking Close call before we flush all messages to HEC
	stream     chan *splunkMessage
	lock       sync.RWMutex
	closed     bool
	closedCond *sync.Cond
}

type splunkLoggerInline struct {
	*splunkLogger

	nullEvent *splunkMessageEvent
}

type splunkLoggerJSON struct {
	*splunkLoggerInline
}

type splunkLoggerHEC struct {
	*splunkLoggerInline
}

type splunkLoggerRaw struct {
	*splunkLogger

	prefix []byte
}

type splunkMessage struct {
	Event      interface{}       `json:"event"`
	Time       string            `json:"time"`
	Host       string            `json:"host"`
	Source     string            `json:"source,omitempty"`
	SourceType string            `json:"sourcetype,omitempty"`
	Index      string            `json:"index,omitempty"`
	Fields     map[string]string `json:"fields,omitempty"`
	Entity     string            `json:"entity,omitempty"`
}

type splunkMessageEvent struct {
	Line   interface{}       `json:"line"`
	Source string            `json:"source"`
	Tag    string            `json:"tag,omitempty"`
	Attrs  map[string]string `json:"attrs,omitempty"`
}

const (
	splunkFormatRaw    = "raw"
	splunkFormatJSON   = "json"
	splunkFormatInline = "inline"
	splunkFormatHEC    = "hec"
)

/*
New Splunk Logger
*/
func New(info logger.Info) (logger.Logger, error) {
	hostname, err := info.Hostname()
	if err != nil {
		return nil, fmt.Errorf("%s: cannot access hostname to set source field", driverName)
	}

	// Parse and validate Splunk URL
	splunkURL, err := parseURL(info)
	if err != nil {
		return nil, err
	}

	// Splunk Token is required parameter
	splunkToken, ok := info.Config[splunkTokenKey]
	if !ok {
		return nil, fmt.Errorf("%s: %s is expected", driverName, splunkTokenKey)
	}

	tlsConfig := &tls.Config{}

	// Splunk is using autogenerated certificates by default,
	// allow users to trust them with skipping verification
	if insecureSkipVerifyStr, ok := info.Config[splunkInsecureSkipVerifyKey]; ok {
		insecureSkipVerify, err := strconv.ParseBool(insecureSkipVerifyStr)
		if err != nil {
			return nil, err
		}
		tlsConfig.InsecureSkipVerify = insecureSkipVerify
	}

	// If path to the root certificate is provided - load it
	if caPath, ok := info.Config[splunkCAPathKey]; ok {
		caCert, err := ioutil.ReadFile(caPath)
		if err != nil {
			return nil, err
		}
		caPool := x509.NewCertPool()
		caPool.AppendCertsFromPEM(caCert)
		tlsConfig.RootCAs = caPool
	}

	if caName, ok := info.Config[splunkCANameKey]; ok {
		tlsConfig.ServerName = caName
	}

	gzipCompression := false
	if gzipCompressionStr, ok := info.Config[splunkGzipCompressionKey]; ok {
		gzipCompression, err = strconv.ParseBool(gzipCompressionStr)
		if err != nil {
			return nil, err
		}
	}

	gzipCompressionLevel := gzip.DefaultCompression
	if gzipCompressionLevelStr, ok := info.Config[splunkGzipCompressionLevelKey]; ok {
		var err error
		gzipCompressionLevel64, err := strconv.ParseInt(gzipCompressionLevelStr, 10, 32)
		if err != nil {
			return nil, err
		}
		gzipCompressionLevel = int(gzipCompressionLevel64)
		if gzipCompressionLevel < gzip.DefaultCompression || gzipCompressionLevel > gzip.BestCompression {
			err := fmt.Errorf("not supported level '%s' for %s (supported values between %d and %d)",
				gzipCompressionLevelStr, splunkGzipCompressionLevelKey, gzip.DefaultCompression, gzip.BestCompression)
			return nil, err
		}
	}

	transport := &http.Transport{
		TLSClientConfig: tlsConfig,
	}
	client := &http.Client{
		Transport: transport,
	}

	source := info.Config[splunkSourceKey]
	sourceType := info.Config[splunkSourceTypeKey]
	if sourceType == "" {
		sourceType = "splunk_connect_docker"
	}
	index := info.Config[splunkIndexKey]

	var nullMessage = &splunkMessage{
		Host:       hostname,
		Source:     source,
		SourceType: sourceType,
		Index:      index,
	}

	// Allow user to remove tag from the messages by setting tag to empty string
	tag := ""
	if tagTemplate, ok := info.Config[tagKey]; !ok || tagTemplate != "" {
		tag, err = loggerutils.ParseLogTag(info, loggerutils.DefaultTemplate)
		if err != nil {
			return nil, err
		}
	}

	attrs, err := info.ExtraAttributes(nil)
	if err != nil {
		return nil, err
	}

	var (
		postMessagesFrequency = getAdvancedOptionDuration(envVarPostMessagesFrequency, defaultPostMessagesFrequency)
		postMessagesBatchSize = getAdvancedOptionInt(envVarPostMessagesBatchSize, defaultPostMessagesBatchSize)
		bufferMaximum         = getAdvancedOptionInt(envVarBufferMaximum, defaultBufferMaximum)
		streamChannelSize     = getAdvancedOptionInt(envVarStreamChannelSize, defaultStreamChannelSize)
	)

	logger := &splunkLogger{
		hec: &hecClient{
			client:                client,
			transport:             transport,
			url:                   splunkURL.String(),
			healthCheckURL:        composeHealthCheckURL(splunkURL),
			auth:                  "Splunk " + splunkToken,
			gzipCompression:       gzipCompression,
			gzipCompressionLevel:  gzipCompressionLevel,
			postMessagesFrequency: postMessagesFrequency,
			postMessagesBatchSize: postMessagesBatchSize,
			bufferMaximum:         bufferMaximum,
		},
		nullMessage: nullMessage,
		stream:      make(chan *splunkMessage, streamChannelSize),
	}

	// By default we don't verify connection, but we allow user to enable that
	verifyConnection := false
	if verifyConnectionStr, ok := info.Config[splunkVerifyConnectionKey]; ok {
		var err error
		verifyConnection, err = strconv.ParseBool(verifyConnectionStr)
		if err != nil {
			return nil, err
		}
	}
	if verifyConnection {
		err = logger.hec.verifySplunkConnection(logger)
		if err != nil {
			return nil, err
		}
	}

	var splunkFormat string
	if splunkFormatParsed, ok := info.Config[splunkFormatKey]; ok {
		switch splunkFormatParsed {
		case splunkFormatInline:
		case splunkFormatJSON:
		case splunkFormatRaw:
		case splunkFormatHEC:
		default:
			return nil, fmt.Errorf("unknown format specified %s, supported formats are inline, json, hec and raw", splunkFormat)
		}
		splunkFormat = splunkFormatParsed
	} else {
		splunkFormat = splunkFormatInline
	}

	var loggerWrapper splunkLoggerInterface

	switch splunkFormat {
	case splunkFormatInline:
		nullEvent := &splunkMessageEvent{
			Tag:   tag,
			Attrs: attrs,
		}

		loggerWrapper = &splunkLoggerInline{logger, nullEvent}
	case splunkFormatJSON:
		nullEvent := &splunkMessageEvent{
			Tag:   tag,
			Attrs: attrs,
		}

		loggerWrapper = &splunkLoggerJSON{&splunkLoggerInline{logger, nullEvent}}
	case splunkFormatHEC:
		nullEvent := &splunkMessageEvent{
			Tag:   tag,
			Attrs: attrs,
		}

		loggerWrapper = &splunkLoggerHEC{&splunkLoggerInline{logger, nullEvent}}
	case splunkFormatRaw:
		var prefix bytes.Buffer
		if tag != "" {
			prefix.WriteString(tag)
			prefix.WriteString(" ")
		}
		for key, value := range attrs {
			prefix.WriteString(key)
			prefix.WriteString("=")
			prefix.WriteString(value)
			prefix.WriteString(" ")
		}

		loggerWrapper = &splunkLoggerRaw{logger, prefix.Bytes()}
	default:
		return nil, fmt.Errorf("unexpected format %s", splunkFormat)
	}

	if getAdvancedOptionBool(envVarSplunkTelemetry, defaultSplunkTelemetry) {
		go telemetry(info, logger, sourceType, splunkFormat)
	}

	go loggerWrapper.worker()

	return loggerWrapper, nil
}

/*
ValidateLogOpt validates the arguments passed in to the plugin
*/
func ValidateLogOpt(cfg map[string]string) error {
	for key := range cfg {
		switch key {
		case splunkURLKey:
		case splunkURLPathKey:
		case splunkTokenKey:
		case splunkSourceKey:
		case splunkSourceTypeKey:
		case splunkIndexKey:
		case splunkCAPathKey:
		case splunkCANameKey:
		case splunkInsecureSkipVerifyKey:
		case splunkFormatKey:
		case splunkVerifyConnectionKey:
		case splunkGzipCompressionKey:
		case splunkGzipCompressionLevelKey:
		case envKey:
		case envRegexKey:
		case labelsKey:
		case tagKey:
		default:
			return fmt.Errorf("unknown log opt '%s' for %s log driver", key, driverName)
		}
	}
	return nil
}

func parseURL(info logger.Info) (*url.URL, error) {
	splunkURLStr, ok := info.Config[splunkURLKey]
	if !ok {
		return nil, fmt.Errorf("%s: %s is expected", driverName, splunkURLKey)
	}

	splunkURL, err := url.Parse(splunkURLStr)
	if err != nil {
		return nil, fmt.Errorf("%s: failed to parse %s as url value in %s", driverName, splunkURLStr, splunkURLKey)
	}

	if !urlutil.IsURL(splunkURLStr) ||
		!splunkURL.IsAbs() ||
		(splunkURL.Path != "" && splunkURL.Path != "/") ||
		splunkURL.RawQuery != "" ||
		splunkURL.Fragment != "" {
		return nil, fmt.Errorf("%s: expected format scheme://dns_name_or_ip:port for %s", driverName, splunkURLKey)
	}

	splunkURLPathStr, ok := info.Config[splunkURLPathKey]
	if !ok {
		splunkURL.Path = "/services/collector/event/1.0"
	} else {
		if strings.HasPrefix(splunkURLPathStr, "/") {
			splunkURL.Path = splunkURLPathStr
		} else {
			return nil, fmt.Errorf("%s: expected format /path/to/collector for %s", driverName, splunkURLPathKey)
		}
	}

	return splunkURL, nil
}

/*
parseURL() makes sure that the URL is the format of: scheme://dns_name_or_ip:port
*/
func composeHealthCheckURL(splunkURL *url.URL) string {
	return splunkURL.Scheme + "://" + splunkURL.Host + "/services/collector/health"
}

func getAdvancedOptionDuration(envName string, defaultValue time.Duration) time.Duration {
	valueStr := os.Getenv(envName)
	if valueStr == "" {
		return defaultValue
	}
	parsedValue, err := time.ParseDuration(valueStr)
	if err != nil {
		logrus.Error(fmt.Sprintf("Failed to parse value of %s as duration. Using default %v. %v", envName, defaultValue, err))
		return defaultValue
	}
	return parsedValue
}

func getAdvancedOptionInt(envName string, defaultValue int) int {
	valueStr := os.Getenv(envName)
	if valueStr == "" {
		return defaultValue
	}
	parsedValue, err := strconv.ParseInt(valueStr, 10, 32)
	if err != nil {
		logrus.Error(fmt.Sprintf("Failed to parse value of %s as integer. Using default %d. %v", envName, defaultValue, err))
		return defaultValue
	}
	return int(parsedValue)
}

func getAdvancedOptionBool(envName string, defaultValue bool) bool {
	valueStr := os.Getenv(envName)
	if valueStr == "" {
		return defaultValue
	}
	parsedValue, err := strconv.ParseBool(valueStr)
	if err != nil {
		logrus.Error(fmt.Sprintf("Failed to parse value of %s as boolean. Using default %v. %v", envName, defaultValue, err))
		return defaultValue
	}
	return bool(parsedValue)
}

// Log() takes in a log message reference and put it into a queue: stream
// stream is used by the HEC workers
func (l *splunkLoggerInline) Log(msg *logger.Message) error {
	message := l.createSplunkMessage(msg)

	event := *l.nullEvent
	event.Line = string(msg.Line)
	event.Source = msg.Source

	message.Event = &event
	logger.PutMessage(msg)
	return l.queueMessageAsync(message)
}

func (l *splunkLoggerJSON) Log(msg *logger.Message) error {
	message := l.createSplunkMessage(msg)
	event := *l.nullEvent

	var rawJSONMessage json.RawMessage
	if err := json.Unmarshal(msg.Line, &rawJSONMessage); err == nil {
		event.Line = &rawJSONMessage
	} else {
		event.Line = string(msg.Line)
	}

	event.Source = msg.Source

	message.Event = &event
	logger.PutMessage(msg)
	return l.queueMessageAsync(message)
}

func (l *splunkLoggerHEC) Log(msg *logger.Message) error {
	message := l.createSplunkMessage(msg)
	event := *l.nullEvent

	if err := json.Unmarshal(msg.Line, &message); err == nil {
		fields := make(map[string]string)
		for k, v := range message.Fields {
			fields[k] = v
		}
		for k, v := range event.Attrs {
			fields[k] = v
		}
		if event.Tag != "" {
			fields["container_tag"] = event.Tag
		}
		message.Fields = fields
	} else {
		event.Line = string(msg.Line)
		event.Source = msg.Source
		message.Event = &event
	}

	logger.PutMessage(msg)
	return l.queueMessageAsync(message)
}

func (l *splunkLoggerRaw) Log(msg *logger.Message) error {
	message := l.createSplunkMessage(msg)

	message.Event = string(append(l.prefix, msg.Line...))
	logger.PutMessage(msg)
	return l.queueMessageAsync(message)
}

func (l *splunkLogger) queueMessageAsync(message *splunkMessage) error {
	l.lock.RLock()
	defer l.lock.RUnlock()
	if l.closedCond != nil {
		return fmt.Errorf("%s: driver is closed", driverName)
	}
	l.stream <- message
	return nil
}

func telemetry(info logger.Info, l *splunkLogger, sourceType string, splunkFormat string) {

	//Send weekly
	waitTime := 7 * 24 * time.Hour
	timer := time.NewTicker(waitTime)
	messageArray := []*splunkMessage{}
	timestamp := strconv.FormatInt(time.Now().UTC().UnixNano()/int64(time.Second), 10)

	type telemetryEvent struct {
		Component string `json:"component"`
		Type      string `json:"type"`
		Data      struct {
			App                     string `json:"app"`
			JsonLogs                bool   `json:"jsonLogs"`
			PartialMsgBufferMaximum int    `json:"partialMsgBufferMaximum"`
			PostMessagesBatchSize   int    `json:"postMessagesBatchSize"`
			PostMessagesFrequency   int    `json:"postMessagesFrequency"`
			SplunkFormat            string `json:"splunkFormat"`
			StreamChannelSize       int    `json:"streamChannelSize"`
			Sourcetype              string `json:"sourcetype"`
		} `json:"data"`
		OptInRequired int64 `json:"optInRequired"`
	}

	telem := &telemetryEvent{}
	telem.Component = "app.connect.docker"
	telem.Type = "event"
	telem.OptInRequired = 2
	telem.Data.App = "splunk_connect_docker"
	telem.Data.Sourcetype = sourceType
	telem.Data.SplunkFormat = splunkFormat
	telem.Data.PostMessagesFrequency = int(getAdvancedOptionDuration(envVarPostMessagesFrequency, defaultPostMessagesFrequency))
	telem.Data.PostMessagesBatchSize = getAdvancedOptionInt(envVarPostMessagesBatchSize, defaultPostMessagesBatchSize)
	telem.Data.StreamChannelSize = getAdvancedOptionInt(envVarStreamChannelSize, defaultStreamChannelSize)
	telem.Data.PartialMsgBufferMaximum = getAdvancedOptionInt(envVarBufferMaximum, defaultBufferMaximum)
	telem.Data.JsonLogs = getAdvancedOptionBool(envVarJSONLogs, defaultJSONLogs)

	var telemMessage = &splunkMessage{
		Host:       "telemetry",
		Source:     "telemetry",
		SourceType: "splunk_connect_telemetry",
		Index:      "_introspection",
		Time:       timestamp,
		Event:      telem,
	}

	messageArray = append(messageArray, telemMessage)

	telemClient := hecClient{
		transport: l.hec.transport,
		client:    l.hec.client,
		auth:      l.hec.auth,
		url:       l.hec.url,
	}

	time.Sleep(5 * time.Second)
	if err := telemClient.tryPostMessages(messageArray); err != nil {
		logrus.Error(err)
	}

	for {
		select {
		case <-timer.C:
			if err := telemClient.tryPostMessages(messageArray); err != nil {
				logrus.Error(err)
			}
		}
	}

}

/*
main function that handles the log stream processing
Do a HEC POST when
- the number of messages matches the batch size
- time out
*/
func (l *splunkLogger) worker() {
	var messages []*splunkMessage
	timer := time.NewTicker(l.hec.postMessagesFrequency)
	for {
		select {
		case message, open := <-l.stream:
			// if the stream channel is closed, post the remaining messages in the buffer
			if !open {
				logrus.Debugf("stream is closed with %d events", len(messages))
				l.hec.postMessages(messages, true)
				l.lock.Lock()
				defer l.lock.Unlock()
				l.hec.transport.CloseIdleConnections()
				l.closed = true
				l.closedCond.Signal()
				return
			}
			messages = append(messages, message)
			// Only sending when we get exactly to the batch size,
			// This also helps not to fire postMessages on every new message,
			// when previous try failed.
			if len(messages)%l.hec.postMessagesBatchSize == 0 {
				messages = l.hec.postMessages(messages, false)
			}
		case <-timer.C:
			logrus.Debugf("messages buffer timeout, sending %d events", len(messages))
			messages = l.hec.postMessages(messages, false)
		}
	}
}

func (l *splunkLogger) Close() error {
	l.lock.Lock()
	defer l.lock.Unlock()
	if l.closedCond == nil {
		l.closedCond = sync.NewCond(&l.lock)
		close(l.stream)
		for !l.closed {
			l.closedCond.Wait()
		}
	}
	return nil
}

func (l *splunkLogger) Name() string {
	return driverName
}

func (l *splunkLogger) createSplunkMessage(msg *logger.Message) *splunkMessage {
	message := *l.nullMessage
	message.Time = fmt.Sprintf("%f", float64(msg.Timestamp.UnixNano())/float64(time.Second))
	return &message
}
