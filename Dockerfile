# start with operating system for Red Hat Openshift
FROM registry.access.redhat.com/ubi8/python-312

COPY ./requirements.txt /opt/app-root/src
RUN cd /opt/app-root/src & \
    pip install -r requirements.txt

# this will invalidate the image layer - copy files
COPY . /opt/app-root/src

# set default flask app and environment
#ENV FLASK_APP app.py
#ENV FLASK_ENV development

# specify ports, host, user
# This is primarily a reminder that we need access to port 5000
EXPOSE 5000

# Change this to UID that matches your username on the host
USER 1001

# launch server
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0"]
