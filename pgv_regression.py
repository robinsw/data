#!/usr/bin/env python

import swat
from dlpy.applications import Sequential
from dlpy.layers import Dense, InputLayer, OutputLayer
from sasctl import Session
from sasctl.tasks import register_model, publish_model


# Connect to the CAS server
s = swat.CAS('dsascontrol', 5570, 'robinswu', 'hp$afm67')

# Upload the training data to CAS
tbl = s.upload('/home/viya/pgv.csv').casTable

# Construct a simple neural network
model = Sequential(conn=s, model_table='dlpy_model')
model.add(InputLayer())
model.add(Dense(n=64))
model.add(Dense(n=32))
model.add(OutputLayer(n=3))

# Train on the sample
model.fit(data=tbl,
          inputs=['SepalLength', 'SepalWidth', 'PetalLength', 'PetalWidth'],
          target='Species',
          max_epochs=50,
          lr=0.001)

# Export the model as an ASTORE and get a reference to the new ASTORE table
s.deeplearn.dlexportmodel(modelTable=model.model_table, initWeights=model.model_weights, casout='astore_table')
astore = s.CASTable('astore_table')

# Connect to the SAS environment
with Session('dsascontrol', 5570, 'robinswu', 'hp$afm67'):
    # Register the trained model by providing:
    #  - the ASTORE containing the model
    #  - a name for the model
    #  - a name for the project
    #
    # NOTE: the force=True option will create the project if it does not exist.
    model = register_model(astore, 'Deep Learning', 'Iris', force=True)

    # Publish the model to SAS® Micro Analytic Service (MAS).  Specifically to
    # the default MAS service "maslocal".
    module = publish_model(model, 'maslocal')

    # sasctl wraps the published module with Python methods corresponding to
    # the various steps defined in the module (like "predict").
    response = module.score(SepalLength=5.1, SepalWidth=3.5,
                            PetalLength=1.4, PetalWidth=0.2)

s.terminate()