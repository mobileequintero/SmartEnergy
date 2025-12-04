# Imagen base oficial AWS Lambda para Python 3.12
FROM public.ecr.aws/lambda/python:3.12

# Optimiza pip
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependencias dentro del runtime de Lambda
COPY requirements.txt .
RUN python -m pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copia tu handler
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Handler
CMD ["lambda_function.lambda_handler"]
