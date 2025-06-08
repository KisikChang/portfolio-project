# 6장용 Dockerfile
# Python 3.10-slim 이미지로 시작
FROM python:3.10-slim  

# Docker 작업 디렉터리 설정 
WORKDIR /code  

# 빌드 컨텍스트 디렉터리에서 Docker 작업 디렉터리로 복사 
COPY requirements.txt /code/  

# requirements 파일에 나열된 Python 라이브러리 설치 
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt  

# 코드 파일과 데이터베이스를 빌드 컨텍스트 디렉터리에서 복사 
COPY *.py /code/  
COPY *.db /code/

# Uvicorn 웹 서버를 시작하고 애플리케이션을 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]  
