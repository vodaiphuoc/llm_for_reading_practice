from typing import List, Dict, Union
from types import NoneType
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, computed_field, Field
import re

@dataclass
class SingleAnswer:
	_order: str
	correct_answer: str
	evidence: List[str]

@dataclass
class SingleQuestion:
	_order: str
	question: str
	options: Dict[str,str]

@dataclass
class Example:
	"""Send to Client"""
	_id: str
	paragraph: str
	question_list: List[SingleQuestion]
	
	@computed_field
	@property
	def num_questions(self)->int:
		return len(self.question_list)

@dataclass
class SingleUserAnswer:
	"""Receive from Client"""
	_order: str
	user_answer: str

@dataclass
class UserResponse:
	"""Receive from Client"""
	_id:str
	response: List[SingleUserAnswer]

@dataclass
class Data2LLM:
	_id: str
	paragraph: str
	question_list: List[SingleQuestion]
	correct_answer_list: list[SingleAnswer]
	user_responses: List[SingleUserAnswer]

	@computed_field
	@property
	def prompt(self)->str:
		total_prompt = f"""
Reading passage:
{{paragraph}}
""".format(paragraph = self.paragraph)

		for question_options, answer, user_answer in zip(self.question_list, 
												self.correct_answer_list, 
												self.user_responses):

			total_prompt += f"""
Question:
{{question}}
Choices:
{{options}}
Correct answer:
{{correct_answer}}
Evidence:
{{evidence}}
My answer:
{{user_answer}}
""".format(question = question_options._order +':'+ question_options.question,
			options = question_options.options,
			correct_answer = answer.correct_answer,
			evidence = answer.evidence,
			user_answer = user_answer.user_answer
			)
		return total_prompt

#### LLM response datatype ####

@dataclass
class SingleModelExplainResponse:
	question: str
	correct_answer: str
	my_answer: str
	evidence: str
	explaination: str

@dataclass
class ModelExplainResponse:
	"""Response to Client"""
	questions: List[SingleModelExplainResponse]
	summarization: str


@dataclass
class ModelContextTranslateResponse:
	context_sentence: str
	transled_context_sentence: str

	@computed_field
	@property
	def string_value(self)->str:
		clean_transled_context_sentence = re.sub(r"\n|\t|\r|\.",'',self.transled_context_sentence).replace('\\','')
		
		return f"""\n Ngoài ra, có thể lấy ví dụ từ đoạn văn, câu `{self.context_sentence}` khi được dịch sang tiếng Việt nghĩa là `{clean_transled_context_sentence}`.""" 

@dataclass
class ModelTranslateResponse:
	"""Response to Client"""
	target_word: str
	translated_word: str
	word_form: str
	describe: str
	example: str

	@computed_field
	@property
	def string_value(self)->str:
		clean_describe = re.sub(r"\n|\t|\r|\.",'', self.describe).replace('\\','')
		clean_example = re.sub(r"\n|\t|\r|\.",'', self.example).replace('\\','')
		return f"""Từ `{self.target_word}` ({self.word_form}) trong tiếng Việt nghĩa là `{self.translated_word}`.<br>Giải thích chi tiết:<br>{clean_describe}<br>Ví dụ trong đặt câu trong Tiếng anh:<br>{clean_example}"""