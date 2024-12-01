import json
from typing import List, Dict, Union
from collections.abc import Iterator
import random
from pydantic.dataclasses import dataclass
from src.data_models import SingleQuestion, Example, SingleAnswer, UserResponse, Data2LLM

class ReadingQuestionLoader(Iterator):
	race_data_path = 'data\\race\\expmrc-race-dev.json'
	idx2alphabet = {0:'A',1:'B', 2:'C', 3:'D', 4:'E', 5:'F'}

	def _pre_setup_master_data(self, total_data: List[Dict[str, str]]):
		return [
			{
				'_id': data['id'],
				'paragraph': data['article'],
				'questions_options': [
								{
									'_order': 'Q'+str(i+1),
									'question': data['questions'][i],
									'options': {self.idx2alphabet[ith]:opt 
													for ith,opt in enumerate(data['options'][i])
												}
								}
								for i in range(len(data['questions']))
							],
				'correct_answer_explaination': [
								{
									'_order': 'Q'+str(i+1),
									'correct_answer': data['answers'][i],
									'evidence': data['evidences'][i],
								}
								for i in range(len(data['questions']))
							]
			}
			for data in total_data
		]

	def __init__(self):
		with open(self.race_data_path, encoding='utf-8', mode ='r') as f:
			race_data: List[Dict[str, str]] = json.load(f)['data']

		self.master_data = self._pre_setup_master_data(race_data)
		self.idx = -1

	def __len__(self):
		return len(self.master_data)

	def __next__(self)->Example:
		self.idx += 1
		if self.idx == self.__len__():
			self.idx = random.choice(list(range(self.__len__())))
		return self.get_example(self.idx)

	def get_example(self, index:int)->Example:
		data_instance = self.master_data[index]
		return Example(
			_id = data_instance['_id'],
			paragraph = data_instance['paragraph'],
			question_list = [SingleQuestion(**q_data) \
				for q_data in data_instance['questions_options']]
		)

	def check_word_in_paragraph(self, para_id:str, target_word:str)->Union[bool, str]:
		for ith, data in enumerate(self.master_data):
			if data['_id'] == para_id:
				query_index = ith

		if query_index is not None:
			para = self.get_example(query_index).paragraph
			
			find_sents = [sent for sent in para.split('.') if target_word in sent or target_word.lower() in  sent]

			if len(find_sents) == 0:
				return False
			else:
				return find_sents[0]
		else:
			raise Exception(f'Cannot find paragraph with input para_id: {para_id}')


	def get_correct_answer(self, index:int)->List[SingleAnswer]:
		data_instance = self.master_data[index]
		return [SingleAnswer(**aw_data)
			for aw_data in data_instance['correct_answer_explaination']
		]

	def getData2LLM(self, user_response: UserResponse)->Data2LLM:
		query_index = None

		for ith, data in enumerate(self.master_data):
			if data['_id'] == user_response._id:
				query_index = ith

		if query_index is not None:
			ex = self.get_example(query_index)
			correct_answer_list = self.get_correct_answer(query_index)


		return Data2LLM(_id = ex._id, 
						paragraph =  ex.paragraph,
						question_list =  ex.question_list,
						correct_answer_list = correct_answer_list,
						user_responses=  user_response.response)