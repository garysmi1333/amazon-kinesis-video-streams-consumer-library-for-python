import json
import configparser
import wave

import boto3
from aiohttp import web

from amazon_kinesis_video_consumer_library.kinesis_video_fragment_processor import KvsFragementProcessor
from amazon_kinesis_video_consumer_library.kinesis_video_streams_parser import KvsConsumerLibrary

config = configparser.ConfigParser()
config.read("config.ini")


to_customer_file = wave.open('audio_to_customer.wav','w')
to_customer_file.setnchannels(1)
to_customer_file.setframerate(8000)
to_customer_file.setsampwidth(2)

from_customer_file = wave.open('audio_from_customer.wav','w')
from_customer_file.setnchannels(1)
from_customer_file.setframerate(8000)
from_customer_file.setsampwidth(2)

aws_access_key_id=config['aws-connect']['aws_access_key_id']
aws_secret_access_key=config['aws-connect']['aws_secret_access_key']
region_name=config['aws-connect']['region_name']


kvs_fragment_processor = KvsFragementProcessor()

kvs_client = boto3.client('kinesisvideo',
                            aws_access_key_id=aws_access_key_id, 
                            aws_secret_access_key=aws_secret_access_key, 
                            region_name=region_name)


def on_fragment_arrived(stream_name, fragment_bytes, fragment_dom, fragment_receive_duration):
    # Should only have to call this once per call
    track_info = kvs_fragment_processor.get_aws_connect_track_info(fragment_dom)
        
    # Depending on how AWS Connect Live Media Streaming is configured the track numbers can be different
    # So make sure we assign the correct ones
    if "AUDIO_FROM_CUSTOMER" in track_info:
        from_customer_track_number = track_info["AUDIO_FROM_CUSTOMER"]['track_number']
        
    if "AUDIO_TO_CUSTOMER" in track_info:
        to_customer_track_number = track_info["AUDIO_TO_CUSTOMER"]['track_number']
    
    # Get the actual audio bytes
    audio_track_data = kvs_fragment_processor.get_aws_connect_customer_audio(fragment_dom)

    # Convert the bytearrays to bytes
    track1_data = bytes(audio_track_data['track_1'])
    track2_data = bytes(audio_track_data['track_2'])

    # And do something with the audio. In this example we are saving it to local file
    if to_customer_track_number == 1:
        if len(track1_data) > 0:
            to_customer_file.writeframes(track1_data)
        if len(track2_data) > 0:
            from_customer_file.writeframes(track2_data)
    else:
        if len(track2_data) > 0:
            to_customer_file.writeframes(track2_data)
        if len(track1_data) > 0:
            from_customer_file.writeframes(track1_data)

def on_stream_read_complete(stream_name): 
    print('stream complete')
    try:
        to_customer_file.close()
    except Exception as e:
        print(e)
    
    try:
        from_customer_file.close()
    except Exception as e:
        print(e)

def on_stream_read_exception(stream_name, error):
    print(f'stream exception {error}')
    try:
        to_customer_file.close()
    except Exception as e:
        print(e)
    try:
        from_customer_file.close()
    except Exception as e:
        print(e)

async def incoming_stream_add(request):
    try:
        aws_incoming_event = await request.json()

        media_streams = aws_incoming_event['Details']['ContactData']['MediaStreams']['Customer']['Audio']
        stream_arn = media_streams['StreamARN']
        
        data_endpoint =kvs_client.get_data_endpoint(
                StreamARN=stream_arn, 
                APIName='GET_MEDIA'
            )
        
        kvs_media_client =  boto3.client('kinesis-video-media', 
                                            aws_access_key_id=aws_access_key_id, 
                                            aws_secret_access_key=aws_secret_access_key, 
                                            region_name=region_name,
                                            endpoint_url=data_endpoint['DataEndpoint'])
        

        get_media_response = kvs_media_client.get_media(
                StreamARN=stream_arn,
                StartSelector={
                    'StartSelectorType': 'NOW'
                }
            )
        
        kvs_consumer = KvsConsumerLibrary(stream_arn, 
                                            get_media_response, 
                                            on_fragment_arrived, 
                                            on_stream_read_complete, 
                                            on_stream_read_exception
                                                )
        kvs_consumer.start()

    except json.decoder.JSONDecodeError as error:
        print(error)
        return web.json_response(status=400)
    return web.json_response(status=204)

app = web.Application()
app.add_routes([web.post('/{stream}',incoming_stream_add)])

if __name__ == '__main__':
    web.run_app(app,host='localhost',port=8000)
