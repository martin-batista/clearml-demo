import os

from random import sample
from clearml import Task

# Connecting ClearML with the current process,
# from here on everything is logged automatically
Task.add_requirements('requirements.txt')
task = Task.init(project_name='ClearML-demo', task_name='Random Hyper-Parameter Search Example', task_type=Task.TaskTypes.optimizer)

# Create a hyper-parameter dictionary for the task
params = {}

# track my parameters dictionary
params = task.connect(params)

# define random search space,
params['batch_size'] = [64, 96, 128, 160, 192]
params['hidden_dims'] = [(128, 128), (512, 512), (32, 32)]

# This is a simple random search 
# (can be integrated with 'bayesian-optimization' 'hpbandster' etc.)
space = {
    'batch_size': lambda: sample(params['batch_size'], 1)[0],
    'hidden_dims': lambda: sample(params['hidden_dims'], 1)[0],
}

# number of random samples to test from 'space'
params['total_number_of_experiments'] = 2

# execution queue to add experiments to
params['execution_queue_name'] = 'default'

# experiment template to optimize with random parameter search
params['experiment_template_name'] = 'Keras HP optimization base'

# Select base template task
# Notice we can be more imaginative and use task_id which will eliminate the need to use project name
template_task = Task.get_task(task_id='ea64f78483864e25bda1aa2e9e8cc4bf')

for i in range(params['total_number_of_experiments']):
    # clone the template task into a new write enabled task (where we can change parameters)
    cloned_task = Task.clone(source_task=template_task, name=f'{template_task.name} {i}', parent=template_task.id)
    cloned_task.add_tags(['HP-Opt'])
    # run it on the GPU queue
    task.execute_remotely('GPU') 

    # get the original template parameters
    cloned_task_parameters = cloned_task.get_parameters()

    # override with random samples form grid
    for k in space:
        cloned_task_parameters[k] = space[k]()

    # put back into the new cloned task
    cloned_task.set_parameters(cloned_task_parameters)
    print(f'Experiment {i} set with parameters {cloned_task_parameters}')

    # enqueue the task for execution
    Task.enqueue(cloned_task.id, queue_name=params['execution_queue_name'])
    print(f'Experiment id={cloned_task.id} enqueue for execution')

# we are done, the next step is to watch the experiments graphs
# Remember to create a default queue if there is none: clearml-agent daemon --queue default
print('Done')