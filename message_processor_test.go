package main

import "testing"

func TestEmptyString(t *testing.T) {
	test := []byte{' '}
	res := isValidEvent(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{' ', ' '}
	res = isValidEvent(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{}
	res = isValidEvent(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{'a'}
	res = isValidEvent(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{1}
	res = isValidEvent(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{87, 65, 84}
	res = isValidEvent(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{0xff, 0xfe, 0xfd} // non utf-8 encodable
	res = isValidEvent(test)

	if res {
		t.Fatalf("%s should be non utf8 decodable", test)
	}
}
