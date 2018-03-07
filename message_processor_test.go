package main

import "testing"

func TestEmptyString(t *testing.T) {
	test := []byte{' '}
	res := shouldSendMessage(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{' ', ' '}
	res = shouldSendMessage(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{}
	res = shouldSendMessage(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{'a'}
	res = shouldSendMessage(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{1}
	res = shouldSendMessage(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{87, 65, 84}
	res = shouldSendMessage(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{0xff, 0xfe, 0xfd} // non utf-8 encodable
	res = shouldSendMessage(test)

	if !res {
		t.Fatalf("%s is non utf8 decodable, but the event should still be sent", test)
	}
}
