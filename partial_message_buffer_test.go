package main

import (
	"os"
	"testing"
	"time"

	"github.com/docker/docker/api/types/plugins/logdriver"
)

func TestAppend(t *testing.T) {
	buf := &partialMsgBuffer{
		bufferTimer: time.Now(),
	}

	entry := &logdriver.LogEntry{
		Source:   "test",
		TimeNano: time.Now().UnixNano(),
		Line:     []byte{'t', 'e', 's', 't'},
		Partial:  false,
	}
	buf.append(entry)

	length1 := buf.tBuf.Len()
	if length1 == 0 {
		t.Fatal("append to partialMsgBuffer failed")
	}

	if buf.bufferReset {
		t.Fatal("bufferReset should be false")
	}

	entry2 := &logdriver.LogEntry{
		Source:   "test",
		TimeNano: time.Now().UnixNano(),
		Line:     []byte{'a', 'b', 'c'},
		Partial:  false,
	}

	buf.append(entry2)

	length2 := buf.tBuf.Len()

	if length2 <= length1 {
		t.Fatal("append to partialMsgBuffer failed on 2nd entry")
	}

	if buf.bufferReset {
		t.Fatal("bufferReset should be false")
	}
}

func TestReset(t *testing.T) {
	buf := &partialMsgBuffer{
		bufferTimer: time.Now(),
	}

	beforeTime := buf.bufferTimer

	entry := &logdriver.LogEntry{
		Source:   "test",
		TimeNano: time.Now().UnixNano(),
		Line:     []byte{'t', 'e', 's', 't'},
		Partial:  false,
	}
	buf.append(entry)

	buf.reset()

	if buf.bufferReset {
		t.Fatal("bufferReset should be false after append()")
	}

	if buf.tBuf.Len() == 0 {
		t.Fatal("tBuf should not be reset if bufferReset is false")
	}

	if buf.bufferTimer != beforeTime {
		t.Fatal("bufferTimer should not be reset if bufferReset is false")
	}

	buf.bufferReset = true
	buf.reset()

	if buf.tBuf.Len() > 0 {
		t.Fatal("tBuf should be reset if bufferReset is false")
	}

	if buf.bufferTimer == beforeTime {
		t.Fatal("bufferTimer should be reset")
	}
}

func TestHasHoldDurationExpired(t *testing.T) {
	test := 5 * time.Millisecond
	if err := os.Setenv(envVarPartialMsgBufferHoldDuration, test.String()); err != nil {
		t.Fatal(err)
	}

	partialMsgBufferHoldDuration = getAdvancedOptionDuration(envVarPartialMsgBufferHoldDuration, defaultPartialMsgBufferHoldDuration)

	startTime := time.Now()
	buf := &partialMsgBuffer{
		bufferTimer: startTime,
	}

	time.Sleep(3 * time.Millisecond)
	endTime := time.Now()
	expired := buf.hasHoldDurationExpired(endTime)
	shouldFlush := buf.shouldFlush(endTime)

	if expired {
		t.Fatal("bufferTimer should not have exipred.")
	}

	if shouldFlush {
		t.Fatal("tbuf should not be flushed")
	}

	time.Sleep(2 * time.Millisecond)
	endTime = time.Now()
	expired = buf.hasHoldDurationExpired(endTime)
	shouldFlush = buf.shouldFlush(endTime)

	if !expired {
		t.Fatal("bufferTimer should have exipred")
	}

	if !shouldFlush {
		t.Fatal("tbuf should be flushed when buffer expired")
	}
}

func TestHasLengthExceeded(t *testing.T) {
	if err := os.Setenv(envVarPartialMsgBufferMaximum, "10"); err != nil {
		t.Fatal(err)
	}
	partialMsgBufferMaximum = getAdvancedOptionInt(envVarPartialMsgBufferMaximum, defaultPartialMsgBufferMaximum)

	buf := &partialMsgBuffer{
		bufferTimer: time.Now(),
	}

	a := []byte{}
	entry := &logdriver.LogEntry{
		Source:   "test",
		TimeNano: time.Now().UnixNano(),
		Line:     a,
		Partial:  false,
	}
	buf.append(entry)
	lengthExceeded := buf.hasLengthExceeded()
	shouldFlush := buf.shouldFlush(time.Now())

	if lengthExceeded {
		t.Fatalf("buffer size should not be exceed with lenth %v", buf.tBuf.Len())
	}

	if shouldFlush {
		t.Fatalf("tbuf should not be flushed with bufferSize %v and current length %v", partialMsgBufferMaximum, buf.tBuf.Len())
	}

	for i := 0; i < 9; i++ {
		a = append(a, 'x')
	}

	entry = &logdriver.LogEntry{
		Source:   "test",
		TimeNano: time.Now().UnixNano(),
		Line:     a,
		Partial:  false,
	}
	buf.append(entry)
	lengthExceeded = buf.hasLengthExceeded()
	shouldFlush = buf.shouldFlush(time.Now())

	if lengthExceeded {
		t.Fatalf("buffer size should not be exceed with lenth %v", buf.tBuf.Len())
	}

	if shouldFlush {
		t.Fatalf("tbuf should not be flushed with bufferSize %v and current length %v", partialMsgBufferMaximum, buf.tBuf.Len())
	}

	a = append(a, 'x')

	entry = &logdriver.LogEntry{
		Source:   "test",
		TimeNano: time.Now().UnixNano(),
		Line:     a,
		Partial:  false,
	}
	buf.append(entry)
	lengthExceeded = buf.hasLengthExceeded()
	shouldFlush = buf.shouldFlush(time.Now())

	if !lengthExceeded {
		t.Fatalf("buffer size should be exceed with lenth %v", buf.tBuf.Len())
	}

	if !shouldFlush {
		t.Fatalf("tbuf should be flushed with bufferSize %v and current length %v", partialMsgBufferMaximum, buf.tBuf.Len())
	}

}
