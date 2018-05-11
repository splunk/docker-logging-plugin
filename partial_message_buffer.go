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
	"time"

	"github.com/Sirupsen/logrus"
	"github.com/docker/docker/api/types/plugins/logdriver"
)

var (
	partialMsgBufferHoldDuration = getAdvancedOptionDuration(envVarPartialMsgBufferHoldDuration, defaultPartialMsgBufferHoldDuration)
	partialMsgBufferMaximum      = getAdvancedOptionInt(envVarPartialMsgBufferMaximum, defaultPartialMsgBufferMaximum)
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
		b.tBuf.Reset()
		b.bufferTimer = time.Now()
	}
}

func (b *partialMsgBuffer) hasHoldDurationExpired(t time.Time) bool {
	diff := t.Sub(b.bufferTimer)
	return diff > partialMsgBufferHoldDuration
}

func (b *partialMsgBuffer) hasLengthExceeded() bool {
	return partialMsgBufferMaximum < b.tBuf.Len()
}

func (b *partialMsgBuffer) shouldFlush(t time.Time) bool {
	return b.hasLengthExceeded() || b.hasHoldDurationExpired(t)
}
