// Package splunk provides the log driver for forwarding server logs to
// Splunk HTTP Event Collector endpoint.
package main

import (
	//"bytes"
	//"compress/gzip"
	//"crypto/tls"
	//"crypto/x509"
	//"encoding/json"
	"fmt"
	//"io"
	//"io/ioutil"
	//"net/http"
	//"net/url"
	"os"
	//"strconv"
	//"sync"
	//"time"

	"github.com/Sirupsen/logrus"
)


var logLevels = map[string]logrus.Level{
	"debug": logrus.DebugLevel,
	"info":  logrus.InfoLevel,
	"warn":  logrus.WarnLevel,
	"error": logrus.ErrorLevel,
}

func main() {
	levelVal := os.Getenv("LOG_LEVEL")
	if levelVal == "" {
		levelVal = "info"
	}
	if level, exists := logLevels[levelVal]; exists {
		logrus.SetLevel(level)
	} else {
		fmt.Fprintln(os.Stderr, "invalid log level: ", levelVal)
		os.Exit(1)
	}

	fmt.Fprintln(os.Stderr, "Not implemented yet...")
	os.Exit(1)
}













