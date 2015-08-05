`mita`
------
A Jenkins slave orchestration service: will poll the queue of a master Jenkins
instance and look for jobs that are stuck and map the labels needed to
configured images ready to get created.

Currently supports only OpenStack as a backend for slave nodes.


About the name
--------------
The ancient Inca empire didn't use any form of slavery and used a taxation
mechanism that mandated public service for all citizens that could perform
labor. And thus, this service ensures that nodes will be up and running (and
will later be terminated) to do some work.
