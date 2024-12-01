"""
LLM tasks:
	- Give explaination to human language
	- Machine translation
"""
from typing import Union, List, Literal
from src.data_models import ModelExplainResponse, ModelTranslateResponse, ModelContextTranslateResponse
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json




class Gemini_Inference(object):
	gemma_prompt = f"<start_of_turn>user\n{{input_prompt}}<end_of_turn><eos>\n"

	exlain_instruction = f"""Please give a detail explaination me as an English learner in the following reading comprehension 
test which describe why need to select the correct answer and why not select my answer if my answer different from 
correct answer. Given a reading passage, questions Q1,Q2, etc.. with multiple choices A,B,C,D..., correct answer 
and my answer, highlight evidence related to the correct answer, please write explaination result and include summarization
of your explaination for my results in your result.
{{prompt_data}}
"""

	translate_instruction = f"""Please translate a word/phrase (in English) in below given user's request into Vietnamese. 
In your result, do the following steps:
1) you must output the word/phrase that user want to translate, put it 'target_word' key of format output
2) translating the word/phrase into Vietnamese word, put it in 'translated_word' key of format output.
3) determine the word form of that target word in English like noun or plural noun, verb or adjective, etc ...,
put in 'word_form' key of format output.
4) write a short brief which shows the meaning of 'target_word', put it in 'describe' key of 
format output.
5) give a sentence example with the word/phrase to shows how to use this word in English, put in 'example' key of format output.

User's request:
{{prompt_data}}
"""

	translate_sent_instruction = f"""Please translate a sentence (in English) in below given user's request 
into Vietnamese. In your result, do the following tasks:
1) Put the sentence in 'context_sentence' key of format output
2) translating the sentence into Vietnamese word, put translated sentence in 'transled_context_sentence' 
key of format output

Sentence:
{{prompt_data}}
"""

	def __init__(self, context_length = 2048):
		load_dotenv()
		genai.configure(api_key=os.environ['gemini_key'])
		self.model = genai.GenerativeModel("gemini-1.5-flash")
		self.context_length = context_length

	def give_explain(self, prompt_data:str)->ModelExplainResponse:
		final_prompt = self.gemma_prompt.format(input_prompt = self.exlain_instruction)
		final_prompt = final_prompt.format(prompt_data = prompt_data)
		response = self.model.generate_content(
			contents = final_prompt, 
			generation_config = genai.GenerationConfig(
				response_mime_type=  "application/json",
				response_schema = ModelExplainResponse)
			)
		return self.post_processing(response.text, task = 'explain')

	def translate(self, user_message:str, use_post_processing:bool = True):
		final_prompt = self.gemma_prompt.format(input_prompt = self.translate_instruction)
		final_prompt = final_prompt.format(prompt_data = user_message)
		response = self.model.generate_content(
			contents = final_prompt, 
			generation_config = genai.GenerationConfig(
				response_mime_type=  "application/json",
				response_schema = ModelTranslateResponse)
			)
		
		if use_post_processing:
			return self.post_processing(model_response = response.text,
										task = 'translate')
		else:
			return response.text	

	def translate_sentence(self, sententce_in_paragraph:str = '', use_post_processing:bool = True):
		final_prompt = self.gemma_prompt.format(input_prompt = self.translate_sent_instruction)
		final_prompt = final_prompt.format(prompt_data = sententce_in_paragraph)
		response = self.model.generate_content(
			contents = final_prompt,
			generation_config = genai.GenerationConfig(
				response_mime_type=  "application/json",
				response_schema = ModelContextTranslateResponse)
		)

		if use_post_processing:
			return self.post_processing(model_response = response.text, 
										context_response = True,
										task = 'translate')
		else:
			return response.text

	def post_processing(self,
		model_response: str,
		task: Literal['explain','translate'],
		context_response: bool = False
		)->Union[ModelExplainResponse, ModelTranslateResponse]:

		reponse_dict = json.loads(model_response)
		if task == 'explain':
			return ModelExplainResponse(**reponse_dict)
		else:
			if context_response:
				return ModelContextTranslateResponse(**reponse_dict)
			else:
				reponse_dict['describe'] = self.translate_sentence(reponse_dict['describe'], 
																	use_post_processing = True).transled_context_sentence
				return ModelTranslateResponse(**reponse_dict)
