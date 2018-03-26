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

import "testing"

func TestShouldSendMessage(t *testing.T) {
	mg := &messageProcessor{}
	test := []byte{' '}
	res := mg.shouldSendMessage(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{' ', ' '}
	res = mg.shouldSendMessage(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{}
	res = mg.shouldSendMessage(test)

	if res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{'a'}
	res = mg.shouldSendMessage(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{1}
	res = mg.shouldSendMessage(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{87, 65, 84}
	res = mg.shouldSendMessage(test)

	if !res {
		t.Fatalf("%s should be empty event", test)
	}

	test = []byte{0xff, 0xfe, 0xfd} // non utf-8 encodable
	res = mg.shouldSendMessage(test)

	if !res {
		t.Fatalf("%s is non utf8 decodable, but the event should still be sent", test)
	}
}
