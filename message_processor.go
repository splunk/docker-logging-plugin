package main

import (
	"bytes"
	"encoding/binary"
	"io"
	"time"
	"unicode/utf8"

	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/api/types/plugins/logdriver"
	"github.com/docker/docker/daemon/logger"
	protoio "github.com/gogo/protobuf/io"
)

var (
	tempMsgBufferHoldDuration = getAdvancedOptionDuration(envVarTempMsgBufferHoldDuration, defaultTempMsgBufferHoldDuration)
	tempMsgBufferMaximum      = getAdvancedOptionInt(envVarTempMsgBufferMaximum, defaultTempMsgBufferMaximum)
)

type messageProcessor struct {
	prevMesssage logdriver.LogEntry
}

func newMessageProcessor() *messageProcessor {
	return &messageProcessor{}
}

func (mg messageProcessor) process(lf *logPair) {
	logrus.Debug("Start to consume log")
	consumeLog(lf)
}

type tmpBuffer struct {
	tBuf                      bytes.Buffer
	bufferTimer               time.Time
	bufferReset               bool
	bufferHoldDurationExpired bool
}

func appendToTempBuffer(p *tmpBuffer, b *logdriver.LogEntry) {
	// Add msg to temp buffer and disable buffer reset flag
	ps, err := p.tBuf.Write(b.Line)
	p.bufferReset = false
	if err != nil {
		logrus.WithError(err).WithField("Appending to Temp Buffer with size:", ps).Error(
			"Error appending to buffer")
	}
}

func resetTempBufferValues(p *tmpBuffer) {
	p.tBuf.Reset()
	p.bufferTimer = time.Now()
	p.bufferHoldDurationExpired = false
}

/*
This is a routine to decode the log stream into LogEntry and store it in buffer
and send the buffer to splunk logger and json logger
*/
func consumeLog(lf *logPair) {
	// Initialize temp buffer
	tmpBuf := &tmpBuffer{
		bufferTimer:               time.Now(),
		bufferReset:               false,
		bufferHoldDurationExpired: false,
	}
	// create a protobuf reader for the log stream
	dec := protoio.NewUint32DelimitedReader(lf.stream, binary.BigEndian, 1e6)
	defer dec.Close()
	// a temp buffer for each log entry
	var buf logdriver.LogEntry
	for {
		// reads a message from the log stream and put it in a buffer until the EOF
		// if there is any other error, recreate the stream reader
		if err := dec.ReadMsg(&buf); err != nil {
			if err == io.EOF {
				logrus.WithField("id", lf.info.ContainerID).WithError(err).Debug("shutting down log logger")
				lf.stream.Close()
				return
			}

			logrus.WithField("id", lf.info.ContainerID).WithError(err).Debug("Ignoring error")
			dec = protoio.NewUint32DelimitedReader(lf.stream, binary.BigEndian, 1e6)
		}

		if shouldSendMessage(buf.Line) {
			// Append to temp buffer
			appendToTempBuffer(tmpBuf, &buf)
			// Check for temp buffer timer expiration
			diff := time.Now().Sub(tmpBuf.bufferTimer)
			if diff > tempMsgBufferHoldDuration {
				tmpBuf.bufferHoldDurationExpired = true
			}

			sendMessage(lf.splunkl, &buf, tmpBuf, lf.info.ContainerID)
			sendMessage(lf.jsonl, &buf, tmpBuf, lf.info.ContainerID)
			//temp buffer and values reset
			if tmpBuf.bufferReset {
				resetTempBufferValues(tmpBuf)
			}
		}
		buf.Reset()
	}
}

// send the log entry message to logger
func sendMessage(l logger.Logger, buf *logdriver.LogEntry, tBuffer *tmpBuffer, containerid string) {
	var msg logger.Message
	if !buf.Partial || tBuffer.bufferHoldDurationExpired || tempMsgBufferMaximum <= tBuffer.tBuf.Len() {
		// Only send if partial bit is not set or temp buffer size reached max or temp buffer timer expired
		logrus.WithField("id", containerid).WithField("Buffer partial flag should be false:",
			buf.Partial).WithField("Temp buffer hold duration expired should be true:",
			tBuffer.bufferHoldDurationExpired).WithField("Temp buffer Length:",
			tBuffer.tBuf.Len()).Debug("Buffer details")
		msg.Line = tBuffer.tBuf.Bytes()
		msg.Source = buf.Source
		msg.Partial = buf.Partial
		msg.Timestamp = time.Unix(0, buf.TimeNano)
		err := l.Log(&msg)

		if err != nil {
			logrus.WithField("id", containerid).WithError(err).WithField("message",
				msg).Error("Error writing log message")
			//Reset temp buffer
			tBuffer.bufferReset = true
		}
		tBuffer.bufferReset = true
	}
}

// shouldSendMessage() returns a boolean indicating
// if the message should be sent to Splunk
func shouldSendMessage(message []byte) bool {
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