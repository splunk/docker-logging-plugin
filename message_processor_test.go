package main

import "testing"

func TestEmptyString(t *testing.T) {
	test := []byte{' '}
	res := isEmptyEvent(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{}
	res = isEmptyEvent(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{'a'}
	res = isEmptyEvent(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{1}
	res = isEmptyEvent(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{87, 65, 84}
	res = isEmptyEvent(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}
}
