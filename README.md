# Amazon Kinesis Video Streams Consumer Library For Python - AWS Connect Example

## Introduction

AWS Connect allows Live Streaming of customer audio to Kinesis Video Streams.

It is then possible to connect to the Kinesis Video Streams and consume the audio for further processing.

This example contains a modified version of the amazon_kinesis_video_consumer_library dealing specifically with
extracting the audio from Kinesis Video Streams generated by an AWS Connect Call Flow.

The Amazon Kinesis Video Stream Consumer Library for Python reads in streaming bytes from Amazon 
Kinesis Video Streams (KVS) made available via a KVS GetMedia or GetMediaForFragmentList API call response. 
The library parses these raw bytes into individual MKV fragments and forwards to call-backs in the user’s application.

Fragments are returned as raw bytes and a searchable DOM like structure by parsing with EMBLite by MideTechnology.

In addition, the KvsFragementProcessor class provides the following functions for post-processing of parsed MKV fragments:
1) get_fragment_tags(): Extract MKV tags from the fragment.
2) get_aws_connect_track_info(): Retrieve the audio track info from the fragment
3) get_aws_connect_customer_audio(): Returns the actual audio bytes from the fragment

## Getting started

An example of how to consume AWS Connect generated Kinesis Video Streams is included in example.py


### To deploy this example:

1. Setup your Call Flow to enable Live Media Streaming https://docs.aws.amazon.com/connect/latest/adminguide/customer-voice-streams.html

2. Setting up the call flow for Live Media Streaming requires creating a Lambda to forward 

2. Make sure you have an active stream running in KVS. The example takes fragments off the live edge of the stream so if 
none are being received the consumer will gracefully exit. If you prefer to parse previous stored fragments, you will need to update the 
StartSelector used in the kvs_consumer_library_example.

3. Clone and CD into this repository
```
git clone https://github.com/garysmi1333/amazon-kinesis-video-streams-consumer-library-for-python.git
cd amazon-kinesis-video-streams-consumer-library-for-python
```

3. Install Python Dependencies:
```
python3 -m pip install -r requirements.txt
```

4. Open the cloned repository with your favourite IDE 

5. In config.ini update your aws credentials:  

6. Run the example code:
```
python3 example.py
```
    The example code starts up a simple http server running on port 8000. The server endpoint /stream receives POST requests
    from the lambda function created when setting up AWS Connect Live Media Streaming
7. The example simply saves the incoming audio to files, to test, make a call to AWS Connect for a short time. 
Two files should be created, to_customer.wav an from_customer.wav either or both will contain audio depending on houw you setup
AWS Connect Live Media Streaming

## Timing and Async Considerations

To keep the examples and base solution as simple as possible, the fragment processing library provided is threaded to 
run outside of the main process but it returns received fragments to the main application process call-backs and isn't
using any asynchronous programming techniques. Therefore, any processing time taken in the on_fragment_arrived() callback
will be blocking for the KVS consumer library fragment processing function. If the processing takes longer (or close to) than the 
fragment duration then the stream processing will slip behind the live edge of the media and introduce additional latency.  

If performing long or external blocking processes in the on_fragment_arrived() callback, it is the responsibility of the 
developer to thread or develop async solutions to prevent extended blocking of the consumer library fragment processing. 


## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## Credits:

[EMBLite by MideTechnology](https://github.com/MideTechnology/ebmlite) is an external EBML parser used to decode the MKV fragents in this library.
For convenance, a slightly modified version of EMBLite is shipped with the KvsConsumerLibrary but adding credit where its due.  
EMBLite MIT License: https://github.com/MideTechnology/ebmlite/blob/development/LICENSE  



