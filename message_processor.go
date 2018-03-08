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

// TODO: implement partial logs and multiline logs logic
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

/*
This is a routine to decode the log stream into LogEntry and store it in buffer
and send the buffer to splunk logger and json logger
*/
func consumeLog(lf *logPair) {
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
		if sendMessage(lf.splunkl, &buf, lf.info.ContainerID) == false {
			continue
		}
		if sendMessage(lf.jsonl, &buf, lf.info.ContainerID) == false {
			continue
		}

		buf.Reset()
	}

}

// send the log entry message to logger
func sendMessage(l logger.Logger, buf *logdriver.LogEntry, containerid string) bool {
	var msg logger.Message
	if !shouldSendMessage(buf.Line) {
		return false
	}

	msg.Line = buf.Line
	msg.Source = buf.Source
	msg.Partial = buf.Partial
	msg.Timestamp = time.Unix(0, buf.TimeNano)
	err := l.Log(&msg)

	if err != nil {
		logrus.WithField("id", containerid).WithError(err).WithField("message", msg).Error("error writing log message")
		return false
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
