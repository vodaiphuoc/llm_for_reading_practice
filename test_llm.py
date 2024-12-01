from src.llms import Gemini_Inference


model = Gemini_Inference()

outputs = model.translate('Physical health nghĩa là gì?')

print(outputs)