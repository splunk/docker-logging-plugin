var protobuf = require('protocol-buffers')
var fs = require('fs')
var net = require('net');
var client = new net.Socket();
var request = require('request');

const stringToWrite = 'helloworld123'
const pipe_file = '/tmp/pipe'
var messages = protobuf(` 
  message LogEntry { 
    string source = 1; 
    int64 time_nano = 2; 
    bytes line = 3; 
    bool partial = 4; 
  } 
`)

const writeToPipe = () => {
    // create a streaming encoder
    var buffer = messages.LogEntry.encode({
        source: 'test',
        time_nano: Date.now() * 1000000,
        line: stringToWrite,
        partial: false
    });

    var buffer2 = Buffer.alloc(4);
    buffer2.writeInt32BE(buffer.length, 0);

    var writeStream = fs.createWriteStream(pipe_file)

    writeStream.write(buffer2);
    writeStream.write(buffer);

    // close the stream
    writeStream.end();
}
writeToPipe();


let reqObj =  {
	"File": pipe_file,
	"Info": {
		"ContainerID": "dfjaksfdaslgsaf1213",
		"Config": {
			"splunk-url": "https://splunk-hec:8088",
			"splunk-token": "00000000-0000-0000-0000-000000000000",
			"splunk-insecureskipverify": "true",
			"splunk-format": "raw"
		},
		"LogPath": "/go/docker-logging-plugin/plugin/rootfs/test.txt"
	}
};

request.post({
    headers: {
        'Content-Type' : 'application/json',
        'Host': 'localhost'
    },
    url:     'http://unix:/run/docker/plugins/splunklog.sock:/LogDriver.StartLogging',
    json:    reqObj
    }, (error, response, body) => {
        console.log(body)
        if (body.Err === '') {
            console.log('Waiting for 10 sec till events get to splunk')
            setTimeout(()=> {
                verifyInSplunk();
            }, 10000);
        }
})


// For the follow http requests
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const url = 'https://splunk-hec:8089'
const verifyInSplunk = () => {
    request.post({
        url: url + '/services/search/jobs?output_mode=json',
        form: {
            earliest_time: '-15m',
            latest_time: 'now',
            search: `search index=main ${stringToWrite}`
        },
        auth: {
            username: 'admin',
            password: 'changeme'
        },
        agentOptions: 'SSL_OP_NO_SSLv3'
    }, (error, res, body) => {
        if (error) {
            console.log("FAILED", error);
            return;
        }
        let result = JSON.parse(body);
        let job_id = result['sid'];
        console.log('sid', job_id)
        console.log('waiting for 2 sec')
        setTimeout(()=> {
            waitToGetResult(job_id)
        }, 2000);
    })
}

const waitToGetResult = (job) => {
    const job_url =  `${url}/services/search/jobs/${job}?output_mode=json`;

    request.get({
        url: job_url,
        auth: {
            username: 'admin',
            password: 'changeme'
        },
        agentOptions: 'SSL_OP_NO_SSLv3'
    }, (err, res, body) => {
        if (err) {
            console.log("FAILED", err);
            return;
        }
        let result = JSON.parse(body);
        if (result['entry'][0]['content']['dispatchState'] !== 'DONE') {
            console.log('FAIL');
            return;
        }
        console.log('dispatchState=DONE')
        getEvents(job);
    })
}

const getEvents = (job) => {
    const event_url = `${url}/services/search/jobs/${job}/events?output_mode=json`;
    request.get({
        url: event_url,
        auth: {
            username: 'admin',
            password: 'changeme'
        },
        agentOptions: 'SSL_OP_NO_SSLv3'
    }, (err, res, body) => {
        if (err) {
            console.log("FAILED", err);
            return;
        }
        let result = JSON.parse(body);
        if (result['results'] && result['results'].length > 0 ) {
            console.log('PASS')
        } else {
            console.log('FAIL: 0 result')
        }
    })
}