# Use an official Python runtime as a parent image
FROM python:3.11

COPY . /Lucy
WORKDIR /Lucy

# run pip install cython
RUN pip install --trusted-host pypi.python.org -r requirements.txt
# RUN cd discord.py;python setup.py install;cd /..

# Run app.py when the container launches
CMD ["python", "bot.py"]