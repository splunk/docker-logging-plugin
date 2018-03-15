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
	partialMsgBufferHoldDuration = getAdvancedOptionDuration(envVarPartialMsgBufferHoldDuration, defaultPartialMsgBufferHoldDuration)
	partialMsgBufferMaximum      = getAdvancedOptionInt(envVarPartialMsgBufferMaximum, defaultPartialMsgBufferMaximum)
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

type pmsgBuffer struct {
	pmsg               bytes.Buffer
	bufferHoldDuration time.Duration
	bufferMaximum      int
	bufferReset        bool
}

func appendToPartialBuffer(p *pmsgBuffer, b *logdriver.LogEntry) {
	// Add msg to partial buffer and disable buffer reset flag
	ps, err := p.pmsg.Write(b.Line)
	p.bufferReset = false
	if err != nil {
		logrus.WithError(err).WithField("Buffer size:", ps).Error("Error appending to buffer")
	}
}

func isPartialBufferHoldDurationExpired(t <-chan time.Time) bool {
	select {
	case <-t:
		return true
	default:
		return false
	}
}

/*
This is a routine to decode the log stream into LogEntry and store it in buffer
and send the buffer to splunk logger and json logger
*/
func consumeLog(lf *logPair) {
	// Initialize partial msg buffer
	pBuf := pmsgBuffer{
		bufferHoldDuration: partialMsgBufferHoldDuration,
		bufferMaximum:      partialMsgBufferMaximum,
		bufferReset:        false,
	}
	//Create timer for pbuffer hold duration
	timer := time.NewTicker(pBuf.bufferHoldDuration)
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
		// Apprend to partial buffer
		appendToPartialBuffer(&pBuf, &buf)
		// Check buffer hold duration
		if isPartialBufferHoldDurationExpired(timer.C) && buf.Partial {
			logrus.Debug("Force partial bit to false due to buffer hold duration expiry")
			buf.Partial = false
		}

		if sendMessage(lf.splunkl, &buf, &pBuf, lf.info.ContainerID) == false {
			continue
		}

		if sendMessage(lf.jsonl, &buf, &pBuf, lf.info.ContainerID) == false {
			continue
		}
		//partial buffer reset
		if pBuf.bufferReset {
			pBuf.pmsg.Reset()
		}
		buf.Reset()
	}
	timer.Stop()
}

// send the log entry message to logger
func sendMessage(l logger.Logger, buf *logdriver.LogEntry, pBuffer *pmsgBuffer, containerid string) bool {
	var msg logger.Message
	if !shouldSendMessage(buf.Line) {
		return false
	}
	if !buf.Partial || pBuffer.bufferMaximum <= pBuffer.pmsg.Len() {
		// Only send if partial bit is not set or partial buffer size reached max
		msg.Line = pBuffer.pmsg.Bytes()
		msg.Source = buf.Source
		msg.Partial = buf.Partial
		msg.Timestamp = time.Unix(0, buf.TimeNano)
		err := l.Log(&msg)

		if err != nil {
			logrus.WithField("id", containerid).WithError(err).WithField("message",
				msg).Error("Error writing log message")
			return false
		}
		pBuffer.bufferReset = true
	}
	return true
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
