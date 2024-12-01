from src.dataloader import ReadingQuestionLoader
from src.llms import Gemini_Inference

from src.data_models import Example, UserResponse, SingleUserAnswer

from fastapi import FastAPI, Request, Response,Form, File, UploadFile, Body, status, Depends
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from typing import List, Any, Annotated, Literal, Union, Dict
from typing import Annotated

import json
import re
from contextlib import asynccontextmanager
from loguru import logger
import asyncio
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("Setting up System")
	app.data_loader = ReadingQuestionLoader()
	app.llm_model = Gemini_Inference()

	yield
	logger.info("Turning down system")
	app.data_loader = None
	app.llm_model = None


app = FastAPI(lifespan = lifespan)
app.mount(path = '/templates', 
          app = StaticFiles(directory='src/front_end/templates', html = True), 
          name='templates')

app.mount(path = '/static', 
          app = StaticFiles(directory='src/front_end/static', html = False), 
          name='static')

origins = [
    "http://localhost",
    "http://localhost:8080/",
    "http://localhost:8000/",
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000"
]
app.add_middleware(CORSMiddleware, 
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"]
                   )
templates = Jinja2Templates(directory='src/front_end/templates')


@app.get("/", response_class=HTMLResponse)
async def index_router(request: Request):
	return templates.TemplateResponse(
		request = request,
		name = "index.html"
		)


@app.get("/getExample", response_class=HTMLResponse)
async def new_example_router(request: Request):
	next_example = next(request.app.data_loader)
	return templates.TemplateResponse(
		request = request,
		name = "reading.html",
		context = {'example': next_example}
		)


@app.post("/getResult", response_class=HTMLResponse)
async def get_result_router(request: Request, 
							reponse_data: UserResponse
							):
	"""
	Ask LLM to write detail explaination given quesition ans answers
	Args:
		response_data: User's answers with datatype 
		```
		@dataclass
		class SingleUserAnswer:
			_order: str
			user_answer: str

		@dataclass
		class UserResponse:
			_id:str
			response: List[SingleUserAnswer]
		```
	Return:
		Explain of LLM model with datatype
		```
		@dataclass
		class SingleModelResponse:
			question: str
			correct_answer: str
			my_answer: str
			evidence: str
			explaination: str

		@dataclass
		class ModelResponse:
			questions: List[SingleModelResponse]
			summarization: str
		```

	"""
	reponse_data._id = reponse_data._id.replace('\n','')

	data2llm = request.app.data_loader.getData2LLM(reponse_data)
	model_response = request.app.llm_model.give_explain(data2llm.prompt)

	return templates.TemplateResponse(
		request = request,
		name = "explain.html",
		context = {'model_response': model_response}
		)

@app.post("/get_message", response_class=JSONResponse)
async def get_user_message_router(request: Request, 
	para_id: Annotated[str, Body()], 
	user_message:Annotated[str, Body()]
	):
	para_id = para_id.replace('\n','')
	model_response = request.app.llm_model.translate(user_message)

	# check if target word is exist in current paragraph or not
	check_result = request.app.data_loader.check_word_in_paragraph(para_id, model_response.target_word)

	if isinstance(check_result,str):
		# Show addition example sentence which contains 'target_word'
		model_sent_response = request.app.llm_model.translate_sentence(check_result)
		return JSONResponse(content = model_response.string_value + model_sent_response.string_value)
	else:
		return JSONResponse(content = model_response.string_value)


async def main_run():
    config = uvicorn.Config("main:app", 
    	port=5000, 
    	log_level="info", 
    	reload=True,
		reload_dirs= ["src/front_end/static", "src/front_end/templates"]
    	)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main_run())