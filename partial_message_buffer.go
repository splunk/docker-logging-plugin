package main

import (
	"bytes"
	"time"

	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/api/types/plugins/logdriver"
)

var (
	tempMsgBufferHoldDuration = getAdvancedOptionDuration(envVarTempMsgBufferHoldDuration, defaultTempMsgBufferHoldDuration)
	tempMsgBufferMaximum      = getAdvancedOptionInt(envVarTempMsgBufferMaximum, defaultTempMsgBufferMaximum)
)

type partialMsgBuffer struct {
	tBuf        bytes.Buffer
	bufferTimer time.Time
	bufferReset bool
}

func (b *partialMsgBuffer) append(l *logdriver.LogEntry) (err error) {
	// Add msg to temp buffer and disable buffer reset flag
	ps, err := b.tBuf.Write(l.Line)
	b.bufferReset = false
	if err != nil {
		logrus.WithError(err).WithField("Appending to Temp Buffer with size:", ps).Error(
			"Error appending to temp buffer")
		b.reset()
		return err
	}
	return nil
}

func (b *partialMsgBuffer) reset() {
	if b.bufferReset {
		logrus.Debug("Resetting temp buffer")
		b.tBuf.Reset()
		b.bufferTimer = time.Now()
	}
}

func (b *partialMsgBuffer) hasHoldDurationExpired(t time.Time) bool {
	diff := t.Sub(b.bufferTimer)
	return diff > tempMsgBufferHoldDuration
}

func (b *partialMsgBuffer) hasLengthExceeded() bool {
	return tempMsgBufferMaximum < b.tBuf.Len()
}

func (b *partialMsgBuffer) shouldFlush(t time.Time) bool {
	return b.hasLengthExceeded() || b.hasHoldDurationExpired(t)
}