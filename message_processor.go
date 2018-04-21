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
	"time"
	"unicode/utf8"

	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/api/types/plugins/logdriver"
	"github.com/docker/docker/daemon/logger"
	protoio "github.com/gogo/protobuf/io"
)

type messageProcessor struct {
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
	// Initialize temp buffer
	tmpBuf := &partialMsgBuffer{
		bufferTimer: time.Now(),
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
			// if err == io.EOF {
			logrus.WithField("id", lf.info.ContainerID).WithError(err).Debug("shutting down log logger")
			lf.stream.Close()
			lf.splunkl.Close()
			return
			// }

			// logrus.WithField("id", lf.info.ContainerID).WithError(err).Debug("Ignoring error")
			// dec = protoio.NewUint32DelimitedReader(lf.stream, binary.BigEndian, 1e6)
		}

		if mg.shouldSendMessage(buf.Line) {
			// Append to temp buffer
			if err := tmpBuf.append(&buf); err == nil {
				// Send message to splunk and json logger
				mg.sendMessage(lf.splunkl, &buf, tmpBuf, lf.info.ContainerID)
				mg.sendMessage(lf.jsonl, &buf, tmpBuf, lf.info.ContainerID)
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
