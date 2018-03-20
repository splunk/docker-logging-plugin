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
}

func (b *tmpBuffer) appendToTempBuffer(l *logdriver.LogEntry) bool {
	// Add msg to temp buffer and disable buffer reset flag
	ps, err := b.tBuf.Write(l.Line)
	b.bufferReset = false
	if err != nil {
		logrus.WithError(err).WithField("Appending to Temp Buffer with size:", ps).Error(
			"Error appending to temp buffer")
		b.resetTempBuffer()
		return false
	}
	return true
}

func (b *tmpBuffer) resetTempBuffer() {
	logrus.Debug("Resetting temp buffer")
	b.tBuf.Reset()
	b.bufferTimer = time.Now()
}

func (b *tmpBuffer) isTempBufferHoldDurationExpired (t time.Time) bool {
	diff := t.Sub(b.bufferTimer)
	return diff > tempMsgBufferHoldDuration
}

func (b *tmpBuffer) isTempBufferLengthExceeded() bool {
	return tempMsgBufferMaximum < b.tBuf.Len()
}

func (b *tmpBuffer) shouldTempBufferFlush(t time.Time) bool {
	return b.isTempBufferLengthExceeded() || b.isTempBufferHoldDurationExpired(t)
}

/*
This is a routine to decode the log stream into LogEntry and store it in buffer
and send the buffer to splunk logger and json logger
*/
func consumeLog(lf *logPair) {
	// Initialize temp buffer
	tmpBuf := &tmpBuffer{
		bufferTimer:               time.Now(),
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
			if tmpBuf.appendToTempBuffer(&buf) {
				// Send message to splunk and json logger
				sendMessage(lf.splunkl, &buf, tmpBuf, lf.info.ContainerID)
				sendMessage(lf.jsonl, &buf, tmpBuf, lf.info.ContainerID)
				//temp buffer and values reset
				if tmpBuf.bufferReset {tmpBuf.resetTempBuffer()}
			}
		}
		buf.Reset()
	}
}

// send the log entry message to logger
func sendMessage(l logger.Logger, buf *logdriver.LogEntry, t *tmpBuffer, containerid string) {
	var msg logger.Message
	// Only send if partial bit is not set or temp buffer size reached max or temp buffer timer expired
	// Check for temp buffer timer expiration
	if !buf.Partial || t.shouldTempBufferFlush(time.Now()) {
		logrus.WithField("id", containerid).WithField("Buffer partial flag should be false:",
			buf.Partial).WithField("Temp buffer Length:", t.tBuf.Len()).Debug("Buffer details")
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