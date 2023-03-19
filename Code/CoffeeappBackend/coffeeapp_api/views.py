import sys
sys.path.append("D:\Programming\master\MAI_NLP_PROJECT")
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import Code.Clients.client_factory as factory

from .question_answering import QuestionAnswerer


class ManufacturerApiView(APIView):
    def get(self, request, *args, **kwargs):
        '''
        maybe all possible manufacturer and models
        '''
        products_by_manufacturer = factory.get_meta_client().get_products_of_all_manufacturers()
        
        return JsonResponse(products_by_manufacturer, safe=False)

class AnswerApiView(APIView):
  
    # def get(self, request, *args, **kwargs):
    #     '''
    #     maybe all possible manufacturer and models
    #     '''
    #     return Response({}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        '''
        maybe all possible manufacturer and models
        '''
        
        questionanswerer = QuestionAnswerer(manufacturer=request.data.get('manufacturer'),
                                            product=request.data.get('product'),
                                            language=request.data.get('language'),
                                            question=request.data.get('question'))
        
        if questionanswerer.is_valid():
            questionanswerer.ask()
            # return JsonResponse(questionanswerer.answers, safe=False)
            return JsonResponse(questionanswerer.answers, safe=False)
            
        
        
        return JsonResponse({"answer": "bad"}, safe=False)
    
    
class TestAnswerApiView(APIView):
  
    def get(self, request, *args, **kwargs):
        '''
        maybe all possible manufacturer and models
        '''
        return Response({}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        '''
        maybe all possible manufacturer and models
        '''
        
        questionanswerer = QuestionAnswerer(manufacturer=request.data.get('manufacturer'),
                                            product=request.data.get('product'),
                                            language=request.data.get('language'),
                                            question=request.data.get('question'))
        
        if questionanswerer.is_valid():
            questionanswerer.ask()
            # return JsonResponse(questionanswerer.answers, safe=False)
            return Response(questionanswerer.answers, status=status.HTTP_200_OK)
            
        return Response({}, status=status.HTTP_400_BAD_REQUEST)