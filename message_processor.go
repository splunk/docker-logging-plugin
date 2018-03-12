package main

import (
	"encoding/binary"
	"io"
	"time"
	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/api/types/plugins/logdriver"
	"github.com/docker/docker/daemon/logger"
	protoio "github.com/gogo/protobuf/io"
	"bytes"
)

// TODO: implement partial logs and multiline logs logic


//var arr = []byte{}

type messageProcessor struct {
	prevMesssage logdriver.LogEntry
}

func newMessageProcessor() *messageProcessor {
	return &messageProcessor{}
}

func (mg messageProcessor) process(lf *logPair) {
	// Initialize partial msg struct
	//pm := partialMessages{}
	pm := pmsgBuffer{}
	//pm.reader = &pm.pmsg
	consumeLog(lf, &pm)
}

//type partialMessages struct {
//	pmsg bufio.Reader
//}

type pmsgBuffer struct {
	//reader io.Reader
	pmsg bytes.Buffer
}

/*
This is a routine to decode the log stream into LogEntry and store it in buffer
and send the buffer to splunk logger and json logger
*/
func consumeLog(lf *logPair, pBuffer *pmsgBuffer) {
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
			dec = protoio.NewUint32DelimitedReader(lf.stream, binary.BigEndian, 1e6)
		}

		if sendMessage(lf.splunkl, &buf, pBuffer, lf.info.ContainerID) == false {
			continue
		}
		if sendMessage(lf.jsonl, &buf, pBuffer, lf.info.ContainerID) == false {
			continue
		}

		buf.Reset()
	}
}

//func readPartialMessages(r io.Reader) []byte {
//	buf := new(bytes.Buffer)
//	buf.ReadFrom(r)
//	return buf.Bytes()
//}

// send the log entry message to logger
func sendMessage(l logger.Logger, buf *logdriver.LogEntry, pBuffer *pmsgBuffer, containerid string) bool {
	var msg logger.Message
	// Add event to partial buffer byte array
	logrus.WithField("id", containerid).WithField("pBuffer.pmsg", buf.Line).Error("buf.Line")
	pBuffer.pmsg.Write(buf.Line)
	//pBuffer.reader.Read(buf.Line)
	logrus.WithField("id", containerid).WithField("pBuffer.pmsg", pBuffer.pmsg.Bytes()).Error("before partial bit checking")
	// Only send if partial bit is not set
	if !buf.Partial {
		logrus.WithField("id", containerid).WithField("pBuffer.pmsg", pBuffer.pmsg.Bytes()).Error("partial bit set")
		msg.Line = pBuffer.pmsg.Bytes()
		msg.Source = buf.Source
		msg.Partial = buf.Partial
		msg.Timestamp = time.Unix(0, buf.TimeNano)
		err := l.Log(&msg)

		if err != nil {
			logrus.WithField("id", containerid).WithError(err).WithField("message", msg).Error("error writing log message")
			return false
		}
		//p = nil
	}
	return true
}
