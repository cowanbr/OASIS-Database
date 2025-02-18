"""
Author: Brison Cowan
Description:

This protocol is for the resin kinetic study. It is an experimental version of the protocol that is maximally modular.
The user can specify the number of source tubes, the time between samples, the lowest and middle depths to aspirate from.

The protocol is designed to be run on an Opentrons OT-2.

The protocol performs the following steps:
1. Initialize samples for source tubes.
2. Wait for a specified time.
3. Take the samples.
4. Repeat steps 2 and 3 until the desired number of samples have been taken.

The protocol uses the following labware in the specified configuration:
-3 sets of 15 mL Falcon tubes in a 15-tube rack : Location 1, 2, 3
-300 uL tips in a 96-tip rack : Location 4
-P300 single-channel pipette
"""

from opentrons import protocol_api

metadata = {
    'apiLevel': '2.18',
    'protocolName': 'ResinKineticStudy_OpentronsOT2',
    'author': "Brison Cowan",
    'description': 'Protocol for transferring and mixing samples. Experimental version.',
    }


def add_parameters(parameters: protocol_api.Parameters):
    # This function
    parameters.add_float(variable_name='time_between_samples', display_name='Time between samples (minutes)',
                         description='Time between each sample collection', default=1, minimum=0, maximum=999)
    parameters.add_int(variable_name='number_of_source_tubes', display_name='Number of source tubes',
                       description='Number of source tubes for the experiment', default=3, minimum=1, maximum=3)
    parameters.add_int(variable_name='lowest_depth', display_name='Lowest depth (mm)',
                       description='The lowest depth to aspirate from', default=1, minimum=0, maximum=100)
    parameters.add_int(variable_name='middle_depth', display_name='Middle depth (mm)',
                       description='The middle depth to aspirate from', default=30, minimum=0, maximum=100)
    parameters.add_int(variable_name='volume_for_transfer', display_name='Volume for transfer (uL)',
                       description='Volume to transfer from source tube to collection tube', default=100,
                       minimum=0, maximum=300)
    parameters.add_int(variable_name='volume_for_mixing', display_name='Volume for mixing (uL)',
                       description='Volume to mix in the source tube', default=200, minimum=0, maximum=300)
    parameters.add_int(variable_name='number_of_mixes', display_name='Number of mixes',
                       description='Number of times to mix the source tube', default=3, minimum=1, maximum=10)
    parameters.add_int(variable_name='number_samples', display_name='Number of samples to collect',
                       description='Number of samples to collect (excluding t_0)', default=13, minimum=0, maximum=13)
    parameters.add_bool(variable_name='skip_mix', display_name='Skip the mixing step?',
                       description='Determines if we are going to mix the samples', default=False)

def run(protocol: protocol_api.ProtocolContext):
    # Parameters
    time_between_samples = protocol.params.time_between_samples
    number_of_source_tubes = protocol.params.number_of_source_tubes
    lowest_depth = protocol.params.lowest_depth
    middle_depth = protocol.params.middle_depth
    volume_for_transfer = protocol.params.volume_for_transfer
    volume_for_mixing = protocol.params.volume_for_mixing
    number_of_mixes = protocol.params.number_of_mixes
    number_samples = protocol.params.number_samples
    skip_mix = protocol.params.skip_mix

    # labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tuberack1 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 1)
    tuberack2 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 2)
    tuberack3 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 3)

    # pipettes
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])


    # reagents
    source_tube_list = []
    for i in range(number_of_source_tubes):
        source_tube_list.append(tuberack1.wells()[i])

    # all tubes
    tubes_list = []
    for i in range(15):
        tubes_list.append(tuberack1.wells()[i])
    for i in range(15):
        tubes_list.append(tuberack2.wells()[i])
    for i in range(15):
        tubes_list.append(tuberack3.wells()[i])

    ####################################################################

    for i in range(number_of_source_tubes):
        # If there is more than 3 source tubes add an increment to the tubes_list index
        take_sample_and_mix(pipette, source_tube_list[i], tubes_list[i + 3],
                            lowest_depth, middle_depth, volume_for_transfer, volume_for_mixing, number_of_mixes, 
                            skip_mix)
    
    for x in range(number_samples):
        # Wait for a specified time
        protocol.delay(minutes=time_between_samples)

        for j in range(number_of_source_tubes):
            take_sample_and_mix(pipette, source_tube_list[j], tubes_list[((x+1)*3)+j+3], lowest_depth, middle_depth,
                                volume_for_transfer, volume_for_mixing, number_of_mixes, skip_mix)
        
def take_sample_and_mix(pipette_name, source_tube, tube, lowest_depth, middle_depth, transfer_volume,
                        mix_volume, number_of_mixes, skip_mix):

    # Pick up the pipette tip
    pipette_name.pick_up_tip()

    # Transfer from source_tube to tube
    pipette_name.aspirate(transfer_volume, source_tube.bottom(middle_depth))  # a little above the bottom of the well
    pipette_name.dispense(transfer_volume, tube.bottom(lowest_depth))  # at the bottom of the well

    if skip_mix == False:
        # Mix the solution in the source_tube, deep in the well
        pipette_name.move_to(source_tube.bottom(lowest_depth))  # Move to the lowest part of the well
        pipette_name.mix(number_of_mixes, mix_volume)  # mix

        # Mix the solution in the source_tube, in the middle of the well
        pipette_name.move_to(source_tube.bottom(middle_depth))  # Move to the middle of the well
        pipette_name.mix(number_of_mixes, mix_volume)  # mix

    # Dump the pipette tip
    pipette_name.drop_tip()