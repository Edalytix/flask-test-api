from flask import Flask,jsonify
from flask_restful import Resource, Api
import speech_recognition as sr
import moviepy.editor as me
import boto3
import os
import pandas as pd
from spacy.lang.en.stop_words import STOP_WORDS
import math
from pydub import AudioSegment
from os import path


app = Flask(__name__)
api=Api(app)


@app.route("/")
def hello_world():
    return "This API generates a CSV file of responses"

class fetch_from_s3(Resource):
    def get(self,bucket_name,response_folder,survey_id,question_id):

        s3_client=boto3.client(
                service_name='s3',
                region_name='us-east-1',
                aws_access_key_id='AKIAUOIG2GGCBPNM2NPH',
                aws_secret_access_key='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' 
            )

        s3_resource=boto3.resource(

                service_name='s3',
                region_name='us-east-1',
                aws_access_key_id='AKIAUOIG2GGCBPNM2NPH',
                aws_secret_access_key='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'
        )

            
        video_content=[]
        video_files_list=[]
        folder_s3_path=response_folder+"/"+survey_id+"/"+question_id+"/"
        audio_files_list=[]
        s3_bucket=s3_resource.Bucket(bucket_name)
        response_from_s3 = s3_client.list_objects(Bucket=bucket_name, Prefix=folder_s3_path)
            
        count=0 
        for content in response_from_s3.get('Contents', []):

            count=count+1
            if count==1:

                continue
            
            obj_path=content.get('Key')
            s3_object_list=obj_path.split('/')
            s3_obj=s3_object_list[-1]

            #print(object_name)
            object_list=s3_obj.split('.')
            print(object_list)
            if object_list[-1]=='mp4' or object_list[-1]=='mpeg':

                if object_list[0] not in video_files_list:
                
                    try:
                        
                        file_path="C:\\Users\\Admin\\Desktop\\Survideo"
                        file_path=file_path+"\\"+s3_obj
                        if os.path.exists(file_path)==True:

                            os.remove(file_path)
                        
                        OUTPUT_AUDIO_FILE = "C:\\Users\\Admin\\Desktop\\Survideo\\converted.wav"
                        if os.path.exists(OUTPUT_AUDIO_FILE)==True:

                            os.remove(OUTPUT_AUDIO_FILE)

                        s3_bucket.download_file(obj_path,file_path)
                        video_clip = me.VideoFileClip(r"{}".format(file_path))
                        video_clip.audio.write_audiofile(r"{}".format(OUTPUT_AUDIO_FILE))
                        recognizer =  sr.Recognizer()
                        audio_clip = sr.AudioFile("{}".format(OUTPUT_AUDIO_FILE))
                        with audio_clip as source:
                            audio_file = recognizer.record(source,duration=video_clip.duration)
                            #print("Please wait ...")
                            result = recognizer.recognize_google(audio_file)
                        video_content.append(result)
                        video_files_list.append(object_list[0])
                        
                        video_clip.close()
                        os.remove(file_path)  
                        os.remove(OUTPUT_AUDIO_FILE)

                    except:

                        pass 
                
                else:

                    pass

            elif object_list[-1]=='wav' or object_list[-1]=='mp3':

                if object_list[0] not in audio_files_list:

                    try:

                    
                        file_path="C:\\Users\\Admin\\Desktop\\Survideo"
                        file_path=file_path+"\\"+s3_obj
                        s3_bucket.download_file(obj_path,file_path)

                        if object_list[-1]=='wav':

                            r = sr.Recognizer()
                            audio_clip = sr.AudioFile("{}".format(file_path))
                            with audio_clip as source:
                                    
                                audio_data = r.record(source)

                            result = r.recognize_google(audio_data)
                            print(result)
                            video_content.append(result)
                            audio_files_list.append(object_list[0])
                            os.remove(file_path)

                        if object_list[-1]=='mp3':
                            
                            
                            output_file="C:\\Users\\Admin\\Desktop\\Survideo"+"\\"+object_list[0]+".wav"
                            #print(file_path)
                            #print(output_file)
                            sound = AudioSegment.from_mp3(file_path)
                            sound.export(output_file, format="wav")
                            r = sr.Recognizer()
                            with sr.AudioFile(output_file) as source:
                                    
                                audio_data = r.record(source)
                            result = r.recognize_google(audio_data)
                            print(result)
                            video_content.append(result)
                            audio_files_list.append(object_list[0])

                            os.remove(file_path)
                            os.remove(output_file)

                    except Exception as e:

                        print(e)

                else:

                    pass

            elif object_list[-1]=='csv':
                
                file_path="C:\\Users\\Admin\\Desktop\\Survideo"
                file_path=file_path+"\\"+s3_obj

                csv_object=s3_bucket.Object(obj_path).get()
                #s3_bucket.download_file(obj_path,file_path)
                csv_file=pd.read_csv(csv_object['Body'])
                video_content=csv_file['response'].tolist()
                

        #print(video_content) 

        summary=get_summary(video_content)
        #return jsonify({"Message":"Got csv file"})
        return jsonify({'Summary': summary})

def get_summary(survey_list):

    # print(len(survey_list))

    clean_survey_list=[]
    punc = '''!()-[]{};:"\,<>./?@#$%^&*_~'''
    stopwords_list=list(STOP_WORDS)
    stopwords_list.remove('give')

    for sentence in survey_list:

        sentence=sentence.replace("n't","")
        for word in sentence:

            if word in punc:

                sentence=sentence.replace(word,"")

            if "’" in word:

                sentence=sentence.replace("’"," '")

            if "'" in word:

                sentence=sentence.replace("'"," '")



        # print(sentence)

        sentence_words=sentence.split()
        # print(sentence_words)
        new_sentence=''

        for words in sentence_words:

            if words.lower() in stopwords_list:

                continue

            if "'t" in words:

                continue

            else:

                new_sentence=new_sentence + ' ' + words

        new_sentence=new_sentence.replace("'","")
        new_sentence=new_sentence.replace("“","")
        new_sentence=new_sentence.replace("”","")
        new_sentence=new_sentence.replace("‘","")

        # print(new_sentence)
        # print("\n")

        clean_survey_list.append(new_sentence)

    word_count={}

    for clean_sentence in clean_survey_list:

        words_in_sent=clean_sentence.split()
        for words in words_in_sent:

            if words.lower() not in word_count.keys():

                word_count[words.lower()]=1

            else:

                word_count[words.lower()]=word_count[words.lower()]+1

    print(word_count)

    value_word_counts=word_count.values()
    max_value=max(value_word_counts)

    #print(max_value)

    for keywords in word_count.keys():

        word_count[keywords.lower()]=(word_count[keywords.lower()]/max_value)

    #print(word_count)

    sentence_importance_score={}

    for sentence in survey_list:

        sentence_words=sentence.split()

        for words in sentence_words:

            if words.lower() in word_count.keys():

                if sentence not in sentence_importance_score.keys():

                    sentence_importance_score[sentence]=1

                else:

                    sentence_importance_score[sentence]=sentence_importance_score[sentence] + word_count[words.lower()]


    #print(sentence_importance_score)   
    
    if len(survey_list)<=10:

        percent_of_sentences=0.2

    else:

        percent_of_sentences=0.15

    num_imp_sentences=math.ceil(len(survey_list)*percent_of_sentences)
    # print(imp_sentences)

    #top_sentences=nlargest(num_imp_sentences,sentence_importance_score,key=sentence_importance_score.get)
    
    sorted_sentences={key:val for key,val in sorted(sentence_importance_score.items(), key=lambda item: item[1],reverse=True)}
    top_n_sentences={}
    count=0
    for key,val in sorted_sentences.items():
        
        count=count+1
        if count<=num_imp_sentences:
            
            top_n_sentences[key]=val
    
    # print(len(top_n_sentences))
    
    top_sentences=list(top_n_sentences.keys())
    summary=''.join(top_sentences)

    return summary

api.add_resource(fetch_from_s3, "/fetch_data/<string:bucket_name>/<string:response_folder>/<string:survey_id>/<string:question_id>")

if __name__=="__main__":

    app.run(debug=True)
