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
	"encoding/binary"
	"io"
	"os"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/api/types/plugins/logdriver"
	"github.com/docker/docker/daemon/logger"
	protoio "github.com/gogo/protobuf/io"
)

const envVarJSONLogs = "SPLUNK_LOGGING_DRIVER_JSON_LOGS"

type messageProcessor struct {
	retryNumber int
}

func (mg messageProcessor) process(lf *logPair) {
	logrus.Debug("Start to consume log")
	mg.consumeLog(lf)
}

/*
This is a routine to decode the log stream into LogEntry and store it in buffer
and send the buffer to splunk logger and json logger
*/
func (mg messageProcessor) consumeLog(lf *logPair) {
	// Check env variable for json logs
	jsonLogs, err := strconv.ParseBool(os.Getenv(envVarJSONLogs))
	if err != nil {
		logrus.WithField("jsonLogs", jsonLogs).WithError(err)
	}

	// Initialize temp buffer
	tmpBuf := &partialMsgBuffer{
		bufferTimer: time.Now(),
	}
	// create a protobuf reader for the log stream
	dec := protoio.NewUint32DelimitedReader(lf.stream, binary.BigEndian, 1e6)
	defer dec.Close()
	defer lf.Close()
	// a temp buffer for each log entry
	var buf logdriver.LogEntry
	curRetryNumber := 0
	for {
		// reads a message from the log stream and put it in a buffer
		if err := dec.ReadMsg(&buf); err != nil {
			// exit the loop if reader reaches EOF or the fifo is closed by the writer
			if err == io.EOF || err == os.ErrClosed || strings.Contains(err.Error(), "file already closed") {
				logrus.WithField("id", lf.info.ContainerID).WithError(err).Info("shutting down loggers")
				return
			}

			// exit the loop if retry number reaches the specified number
			if mg.retryNumber != -1 && curRetryNumber > mg.retryNumber {
				logrus.WithField("id", lf.info.ContainerID).WithField("curRetryNumber", curRetryNumber).WithField("retryNumber", mg.retryNumber).WithError(err).Error("Stop retrying. Shutting down loggers")
				return
			}

			// if there is any other error, retry for robustness. If retryNumber is -1, retry forever
			curRetryNumber++
			logrus.WithField("id", lf.info.ContainerID).WithField("curRetryNumber", curRetryNumber).WithField("retryNumber", mg.retryNumber).WithError(err).Error("Encountered error and retrying")
			time.Sleep(500 * time.Millisecond)
			dec = protoio.NewUint32DelimitedReader(lf.stream, binary.BigEndian, 1e6)
		}
		curRetryNumber = 0

		if mg.shouldSendMessage(buf.Line) {
			if tmpBuf.tBuf.Len() == 0 {
				logrus.Debug("First messaging, reseting timer")
				tmpBuf.bufferTimer = time.Now()
			}
			// Append to temp buffer
			if err := tmpBuf.append(&buf); err == nil {
				// Send message to splunk and also json logger if enabled
				mg.sendMessage(lf.splunkl, &buf, tmpBuf, lf.info.ContainerID)
				if jsonLogs {
					mg.sendMessage(lf.jsonl, &buf, tmpBuf, lf.info.ContainerID)
				}
				//temp buffer and values reset
				tmpBuf.reset()
			}
		}
		buf.Reset()
	}
}

// send the log entry message to logger
func (mg messageProcessor) sendMessage(l logger.Logger, buf *logdriver.LogEntry, t *partialMsgBuffer, containerid string) {
	var msg logger.Message
	// Only send if partial bit is not set or temp buffer size reached max or temp buffer timer expired
	// Check for temp buffer timer expiration
	if !buf.Partial || t.shouldFlush(time.Now()) {
		msg.Line = t.tBuf.Bytes()
		msg.Source = buf.Source
		msg.Partial = buf.Partial
		msg.Timestamp = time.Unix(0, buf.TimeNano)

		if err := l.Log(&msg); err != nil {
			logrus.WithField("id", containerid).WithError(err).WithField("message",
				msg).Error("Error writing log message")
		}
		t.bufferReset = true
	}
}

// shouldSendMessage() returns a boolean indicating
// if the message should be sent to Splunk
func (mg messageProcessor) shouldSendMessage(message []byte) bool {
	trimedLine := bytes.Fields(message)
	if len(trimedLine) == 0 {
		logrus.Info("Ignoring empty string")
		return false
	}

	// even if the message byte array is not a valid utf8 string
	// we are still sending the message to splunk
	if !utf8.Valid(message) {
		logrus.Warnf("%v is not UTF-8 decodable", message)
		return true
	}
	return true
}
