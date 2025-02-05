from opentrons import protocol_api

metadata = {
    'apiLevel': '2.15',
    'protocolName': 'ResinKineticStudy_OpentronsOT2',
    'author': "Brison Cowan",
    'description': 'Protocol for transferring and mixing samples.',
    }


def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(variable_name='time_between_samples', display_name='Time between samples (minutes)',
                       description='Time between each sample collection', default=1, minimum=0, maximum=90)
    parameters.add_int(variable_name='lowest_depth', display_name='Lowest depth (mm)',
                       description='The lowest depth to aspirate from', default=1, minimum=0, maximum=100)
    parameters.add_int(variable_name='middle_depth', display_name='Middle depth (mm)',
                       description='The middle depth to aspirate from', default=30, minimum=0, maximum=100)
    parameters.add_int(variable_name='volume_for_transfer', display_name='Volume for transfer (uL)',
                       description='Volume to transfer from source tube to collection tube', default=100,
                       minimum=0, maximum=1000)
    parameters.add_int(variable_name='volume_for_mixing', display_name='Volume for mixing (uL)',
                       description='Volume to mix in the source tube', default=200, minimum=0, maximum=1000)
    parameters.add_int(variable_name='number_of_mixes', display_name='Number of mixes',
                       description='Number of times to mix the source tube', default=3, minimum=1, maximum=10)


def run(protocol: protocol_api.ProtocolContext):
    # Parameters
    time_between_samples = protocol.params.time_between_samples
    lowest_depth = protocol.params.lowest_depth
    middle_depth = protocol.params.middle_depth
    volume_for_transfer = protocol.params.volume_for_transfer
    volume_for_mixing = protocol.params.volume_for_mixing
    number_of_mixes = protocol.params.number_of_mixes

    collections = 39    # number of collections taken. Don't change this number unless you are Brison.

    # labware
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tuberack1 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 1)
    tuberack2 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 2)
    tuberack3 = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 3)

    # pipettes
    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # reagents
    source_tube_1 = tuberack1.wells()[0]
    source_tube_2 = tuberack1.wells()[1]
    source_tube_3 = tuberack1.wells()[2]

    # tubes for t0 min
    tube_t0_1 = tuberack1.wells()[3]
    tube_t0_2 = tuberack1.wells()[4]
    tube_t0_3 = tuberack1.wells()[5]

    # tubes for standard collection
    tubes_list = []
    for i in range(6, 15):
        tubes_list.append(tuberack1.wells()[i])
    for i in range(15):
        tubes_list.append(tuberack2.wells()[i])
    for i in range(15):
        tubes_list.append(tuberack3.wells()[i])

    ####################################################################

    # Initialize samples for source_tubes
    take_sample_and_mix(pipette, source_tube_1, tube_t0_1, lowest_depth, middle_depth, volume_for_transfer,
                        volume_for_mixing, number_of_mixes)
    take_sample_and_mix(pipette, source_tube_2, tube_t0_2, lowest_depth, middle_depth, volume_for_transfer,
                        volume_for_mixing, number_of_mixes)
    take_sample_and_mix(pipette, source_tube_3, tube_t0_3, lowest_depth, middle_depth, volume_for_transfer,
                        volume_for_mixing, number_of_mixes)

    for i in range(0, collections, 3):
        # Wait for a specified time
        protocol.delay(minutes=time_between_samples)

        # Take the samples
        take_sample_and_mix(pipette, source_tube_1, tubes_list[i], lowest_depth, middle_depth, volume_for_transfer,
                            volume_for_mixing, number_of_mixes)
        take_sample_and_mix(pipette, source_tube_2, tubes_list[i+1], lowest_depth, middle_depth, volume_for_transfer,
                            volume_for_mixing, number_of_mixes)
        take_sample_and_mix(pipette, source_tube_3, tubes_list[i+2], lowest_depth, middle_depth, volume_for_transfer,
                            volume_for_mixing, number_of_mixes)


def take_sample_and_mix(pipette_name, source_tube, tube, lowest_depth, middle_depth, transfer_volume,
                        mix_volume, number_of_mixes):
    # Pick up the pipette tip
    pipette_name.pick_up_tip()

    # Transfer from source_tube to tube
    pipette_name.aspirate(transfer_volume, source_tube.bottom(middle_depth))  # a little above the bottom of the well
    pipette_name.dispense(transfer_volume, tube.bottom(lowest_depth))  # at the bottom of the well

    # Mix the solution in the source_tube, deep in the well
    pipette_name.move_to(source_tube.bottom(lowest_depth))  # Move to the lowest part of the well
    pipette_name.mix(number_of_mixes, mix_volume)  # mix

    # Mix the solution in the source_tube, in the middle of the well
    pipette_name.move_to(source_tube.bottom(middle_depth))  # Move to the middle of the well
    pipette_name.mix(number_of_mixes, mix_volume)  # mix

    # Dump the pipette tip
    pipette_name.drop_tip()