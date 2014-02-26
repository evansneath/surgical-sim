#!/usr/bin/env python

"""Network module

Contains the neural network class for regression training and testing of the
surgicalsim environment.

Author:
    Evan Sneath - evansneath@gmail.com

License:
    Open Software License v3.0

Classes:
    LongTermPlanningNetwork: Recurrent LSTM neural network class for path prediction.
    LongTermPlanningTrainer: Neural network trainer for path prediction network.
"""

import copy
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Import pybrain neural network and trainer modules
from pybrain.supervised.evolino.networkwrapper import EvolinoNetwork
from pybrain.supervised.trainers.evolino import EvolinoTrainer

from pybrain.tools.customxml.networkwriter import NetworkWriter
from pybrain.tools.customxml.networkreader import NetworkReader

import surgicalsim.lib.constants as constants
import surgicalsim.lib.datastore as datastore
import surgicalsim.lib.pathutils as pathutils


class LongTermPlanningNetwork(EvolinoNetwork):
    """PathPlanningNetwork class

    The primary path planning network for the surgicalsim testing environment.

    Methods:
        save_network_to_file: Stores the network in an xml file.
        load_netowrk_from_file: Loads the network from a written xml file.

    Inherits:
        EvolinoNetwork: The PyBrain built-in Evolino network configuration.
    """
    def __init__(self, indim=None, outdim=None, hiddim=None):
        """Initialize

        Creates a new Long Term Planning Neural Network for use in the
        neuralsim simulation environment.

        Arguments:
            indim: Number of inputs to the neural network.
                (Default: G_LT_NUM_INPUTS listed in surgicalsim.lib.constants)
            outdim: Number of outputs to the neural network.
                (Default: G_LT_NUM_OUTPUTS listed in surgicalsim.lib.constants)
            hiddim: Number of hidden nodes in the neural network.
                (Default: G_NUM_HIDDEN_NODES listed in surgicalsim.lib.constants)
        """
        if indim is None:
            indim = constants.G_LT_NUM_INPUTS

        if outdim is None:
            outdim = constants.G_LT_NUM_OUTPUTS

        if hiddim is None:
            hiddim = constants.G_NUM_HIDDEN_NODES

        super(LongTermPlanningNetwork, self).__init__(indim, outdim, hiddim)

        return

    def save_network_to_file(self, filename):
        """Save Network to File

        Saves the neural network including all connection weights into a
        NetworkWriter format xml file for future loading.

        Arguments:
            filename: The filename into which the network should be saved.
        """
        NetworkWriter.writeToFile(self._network, filename)

        return

    def load_network_from_file(self, filename):
        """Load Network from File

        Using a NetworkWriter written file, data from the saved network
        will be reconstituted into a new LongTermPlanningNetwork class.
        This is used to load saved networks.

        Arguments:
            filename: The filename of the saved xml file.
        """
        self._network = NetworkReader.readFrom(filename)

        return


class LongTermPlanningTrainer(EvolinoTrainer):
    """PathPlanningTrainer class

    Responsible for training the LongTermPlanningNetwork neural network
    for use in the surgicalsim testing environment.

    Inherits:
        EvolinoTrainer: The PyBrain built-in Evolino trainer class.
    """
    pass


def train_lt_network():
    """Train Long-Term Network

    Trains an Evolino LSTM neural network for long-term path planning for
    use in the surgical simulator.

    Returns:
        A copy of the fully-trained path planning neural network.
    """
    # Build up the list of files to use as training set
    filepath = '../results/'

    training_filenames = [
        'sample1.dat',
        'sample2.dat',
        'sample3.dat',
        'sample4.dat',
        'sample5.dat',
    ]

    #testing_filename = 'sample5.dat'

    # Get the training data and place it into a dataset
    training_dataset = None

    # Store all training set ratings
    ratings = np.array([])

    for training_filename in training_filenames:
        training_file = filepath + training_filename
        training_data = datastore.retrieve(training_file)

        # Normalize the time input of the data
        training_data = pathutils.normalize_time(training_data, t_col=constants.G_TIME_IDX)

        # Add this data sample to the training dataset
        training_dataset = datastore.list_to_dataset(
            training_data[:,constants.G_LT_INPUT_IDX:constants.G_LT_INPUT_IDX+constants.G_LT_NUM_INPUTS],
            training_data[:,constants.G_LT_OUTPUT_IDX:constants.G_LT_OUTPUT_IDX+constants.G_LT_NUM_OUTPUTS],
            dataset=training_dataset
        )

        # Store the rating of the data
        this_rating = training_data[1:,constants.G_RATING_IDX]
        ratings = np.hstack((ratings, this_rating))


    # Get the starting point information for testing
    pos_start_idx = constants.G_POS_IDX
    pos_end_idx = pos_start_idx + constants.G_NUM_POS_DIMS

    pos_start = training_data[0,pos_start_idx:pos_end_idx]
    
    # Get the time sequence input data for testing
    time_steps = 1000
    t_input = np.linspace(start=0.0, stop=1.0, num=time_steps)
    t_input = np.reshape(t_input, (len(t_input), 1))

    gate_start_idx = constants.G_GATE_IDX
    gate_end_idx = gate_start_idx + constants.G_NUM_GATE_INPUTS

    # Pull the gate data from the last training dataset
    gate_data = training_data[0:1,gate_start_idx:gate_end_idx]
    gate_data = np.tile(gate_data, (time_steps, 1))

    # Get testing data
    #testing_file = filepath + testing_filename
    #testing_data = datastore.retrieve(testing_file)

    #testing_data = pathutils.normalize_time(testing_data, t_col=constants.G_TIME_IDX)

    ## Store the testing data in a datastore object
    #testing_dataset = datastore.list_to_dataset(
    #    testing_data[:,constants.G_LT_INPUT_IDX:constants.G_LT_INPUT_IDX+constants.G_LT_NUM_INPUTS],
    #    testing_data[:,constants.G_LT_OUTPUT_IDX:constants.G_LT_OUTPUT_IDX+constants.G_LT_NUM_OUTPUTS],
    #    dataset=None
    #)

    # Build up a full ratings matrix
    nd_ratings = None

    for rating in ratings:
        this_rating = rating * np.ones((1, constants.G_LT_NUM_OUTPUTS))

        if nd_ratings is None:
            nd_ratings = this_rating
        else:
            nd_ratings = np.vstack((nd_ratings, this_rating))

    # Create network and trainer
    print('>>> Building Network...')
    net = LongTermPlanningNetwork()

    print('>>> Initializing Trainer...')
    trainer = LongTermPlanningTrainer(
        evolino_network=net,
        dataset=training_dataset,
        nBurstMutationEpochs=10,
        importance=nd_ratings
    )

    # Begin the training iterations
    fitness_list = []
    max_fitness = None
    max_fitness_epoch = None

    # Draw the generated path plot
    fig = plt.figure(1, facecolor='white')
    testing_axis = fig.add_subplot(111, projection='3d')

    fig.show()

    # Define paramters for convergence
    MAX_ITERATIONS = 30#100
    CONVERGENCE_THRESHOLD = -0.00005
    REQUIRED_CONVERGENCE_STREAK = 10

    idx = 0
    current_convergence_streak = 0
    
    while True:
        print('>>> Training Network (Iteration: %3d)...' % (idx+1))
        trainer.train()

        # Determine fitness of this network
        current_fitness = trainer.evaluation.max_fitness
        fitness_list.append(current_fitness)

        print('>>> FITNESS: %f' % current_fitness)

        # Determine if this is the minimal error network
        if max_fitness is None or max_fitness < current_fitness:
            # This is the minimum, record it
            max_fitness = current_fitness
            max_fitness_epoch = idx

        # Draw the generated path after training
        print('>>> Testing Network...')
        #washout_ratio = 1.0 / len(testing_data)
        #_, generated_output, _ = net.calculateOutput(testing_dataset,
        #        washout_ratio=washout_ratio)

        generated_output = net.extrapolate(t_input, [pos_start], len(t_input)-1)
        generated_output = np.vstack((pos_start, generated_output))

        #generated_input = testing_data[:len(generated_output),:constants.G_TOTAL_NUM_INPUTS]

        generated_input = np.hstack((t_input, gate_data))

        # Smash together the input and output
        generated_data = np.hstack((generated_input, generated_output))

        print('>>> Drawing Generated Path...')
        pathutils.display_path(testing_axis, generated_data, title='Generated Testing Path')
       
        plt.draw()

        if current_fitness > CONVERGENCE_THRESHOLD:
            # We've encountered a fitness higher than threshold
            current_convergence_streak += 1
        else:
            # Streak ended. Reset the streak counter
            current_convergence_streak = 0

        if current_convergence_streak == REQUIRED_CONVERGENCE_STREAK:
            print('>>> Convergence Achieved: %d Iterations' % idx)
            break
        elif idx == MAX_ITERATIONS - 1:
            print('>>> Reached maximum iterations (%d)' % MAX_ITERATIONS)
            break

        idx += 1

    # Draw the iteration fitness plot
    plt.figure(facecolor='white')
    plt.cla()
    plt.title('Fitness of RNN over %d Iterations' % (idx-1))
    plt.xlabel('Training Iterations')
    plt.ylabel('Fitness')
    plt.grid(True)

    plt.plot(range(len(fitness_list)), fitness_list, 'r-')

    plt.annotate('local max', xy=(max_fitness_epoch, fitness_list[max_fitness_epoch]),
            xytext=(max_fitness_epoch, fitness_list[max_fitness_epoch]+0.01),
            arrowprops=dict(facecolor='black', shrink=0.05))

    plt.show()

    # Return a full copy of the trained neural network
    return copy.deepcopy(net)


if __name__ == '__main__':
    # Module default - Trains the neural network and saves it to a file
    import sys
    import os.path

    # Train the long-term neural network
    net = train_lt_network()

    DEFAULT_FILENAME = './lt-network.xml'

    filename = DEFAULT_FILENAME

    if len(sys.argv) > 1:
        if not os.path.exists(sys.argv[1]):
            print('>>> ERROR: Could not open given filename')
        else:
            filename = sys.argv[1]

    print('>>> Writing network to %s' % filename)

    # Dump the learned neural network to a file in this directory
    net.save_network_to_file(filename)

    print ('>>> Done')

    exit()
