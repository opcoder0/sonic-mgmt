# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: nic_simulator_grpc_mgmt_service.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import nic_simulator_grpc_service_pb2 as nic__simulator__grpc__service__pb2     # noqa: E402 F401


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%nic_simulator_grpc_mgmt_service.proto\x1a nic_simulator_grpc_service.proto\"R\n\x12ListOfAdminRequest\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12%\n\x0e\x61\x64min_requests\x18\x02 \x03(\x0b\x32\r.AdminRequest\"M\n\x10ListOfAdminReply\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12\"\n\radmin_replies\x18\x02 \x03(\x0b\x32\x0b.AdminReply\"^\n\x16ListOfOperationRequest\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12-\n\x12operation_requests\x18\x02 \x03(\x0b\x32\x11.OperationRequest\"Y\n\x14ListOfOperationReply\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12*\n\x11operation_replies\x18\x02 \x03(\x0b\x32\x0f.OperationReply\"O\n\x11ListOfDropRequest\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12#\n\rdrop_requests\x18\x02 \x03(\x0b\x32\x0c.DropRequest\"J\n\x0fListOfDropReply\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12 \n\x0c\x64rop_replies\x18\x02 \x03(\x0b\x32\n.DropReply\"O\n ListOfNiCServerAdminStateRequest\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12\x14\n\x0c\x61\x64min_states\x18\x02 \x03(\x08\"`\n\x1eListOfNiCServerAdminStateReply\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12\x14\n\x0c\x61\x64min_states\x18\x02 \x03(\x08\x12\x11\n\tsuccesses\x18\x03 \x03(\x08\"e\n\x18ListOfFlapCounterRequest\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12\x32\n\x15\x66lap_counter_requests\x18\x02 \x03(\x0b\x32\x13.FlapCounterRequest\"`\n\x16ListOfFlapCounterReply\x12\x15\n\rnic_addresses\x18\x01 \x03(\t\x12/\n\x14\x66lap_counter_replies\x18\x02 \x03(\x0b\x32\x11.FlapCounterReply2\x9c\x04\n\x12\x44ualTorMgmtService\x12I\n\x1dQueryAdminForwardingPortState\x12\x13.ListOfAdminRequest\x1a\x11.ListOfAdminReply\"\x00\x12G\n\x1bSetAdminForwardingPortState\x12\x13.ListOfAdminRequest\x1a\x11.ListOfAdminReply\"\x00\x12K\n\x17QueryOperationPortState\x12\x17.ListOfOperationRequest\x1a\x15.ListOfOperationReply\"\x00\x12\x31\n\x07SetDrop\x12\x12.ListOfDropRequest\x1a\x10.ListOfDropReply\"\x00\x12^\n\x16SetNicServerAdminState\x12!.ListOfNiCServerAdminStateRequest\x1a\x1f.ListOfNiCServerAdminStateReply\"\x00\x12H\n\x10QueryFlapCounter\x12\x19.ListOfFlapCounterRequest\x1a\x17.ListOfFlapCounterReply\"\x00\x12H\n\x10ResetFlapCounter\x12\x19.ListOfFlapCounterRequest\x1a\x17.ListOfFlapCounterReply\"\x00\x62\x06proto3')     # noqa: E501


_LISTOFADMINREQUEST = DESCRIPTOR.message_types_by_name['ListOfAdminRequest']
_LISTOFADMINREPLY = DESCRIPTOR.message_types_by_name['ListOfAdminReply']
_LISTOFOPERATIONREQUEST = DESCRIPTOR.message_types_by_name['ListOfOperationRequest']
_LISTOFOPERATIONREPLY = DESCRIPTOR.message_types_by_name['ListOfOperationReply']
_LISTOFDROPREQUEST = DESCRIPTOR.message_types_by_name['ListOfDropRequest']
_LISTOFDROPREPLY = DESCRIPTOR.message_types_by_name['ListOfDropReply']
_LISTOFNICSERVERADMINSTATEREQUEST = DESCRIPTOR.message_types_by_name[
    'ListOfNiCServerAdminStateRequest']
_LISTOFNICSERVERADMINSTATEREPLY = DESCRIPTOR.message_types_by_name[
    'ListOfNiCServerAdminStateReply']
_LISTOFFLAPCOUNTERREQUEST = DESCRIPTOR.message_types_by_name['ListOfFlapCounterRequest']
_LISTOFFLAPCOUNTERREPLY = DESCRIPTOR.message_types_by_name['ListOfFlapCounterReply']
ListOfAdminRequest = _reflection.GeneratedProtocolMessageType('ListOfAdminRequest', (_message.Message,), {
    'DESCRIPTOR': _LISTOFADMINREQUEST,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfAdminRequest)
})
_sym_db.RegisterMessage(ListOfAdminRequest)

ListOfAdminReply = _reflection.GeneratedProtocolMessageType('ListOfAdminReply', (_message.Message,), {
    'DESCRIPTOR': _LISTOFADMINREPLY,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfAdminReply)
})
_sym_db.RegisterMessage(ListOfAdminReply)

ListOfOperationRequest = _reflection.GeneratedProtocolMessageType('ListOfOperationRequest', (_message.Message,), {
    'DESCRIPTOR': _LISTOFOPERATIONREQUEST,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfOperationRequest)
})
_sym_db.RegisterMessage(ListOfOperationRequest)

ListOfOperationReply = _reflection.GeneratedProtocolMessageType('ListOfOperationReply', (_message.Message,), {
    'DESCRIPTOR': _LISTOFOPERATIONREPLY,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfOperationReply)
})
_sym_db.RegisterMessage(ListOfOperationReply)

ListOfDropRequest = _reflection.GeneratedProtocolMessageType('ListOfDropRequest', (_message.Message,), {
    'DESCRIPTOR': _LISTOFDROPREQUEST,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfDropRequest)
})
_sym_db.RegisterMessage(ListOfDropRequest)

ListOfDropReply = _reflection.GeneratedProtocolMessageType('ListOfDropReply', (_message.Message,), {
    'DESCRIPTOR': _LISTOFDROPREPLY,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfDropReply)
})
_sym_db.RegisterMessage(ListOfDropReply)

ListOfNiCServerAdminStateRequest = _reflection.GeneratedProtocolMessageType('ListOfNiCServerAdminStateRequest', (_message.Message,), {                          # noqa: E501
    'DESCRIPTOR': _LISTOFNICSERVERADMINSTATEREQUEST,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfNiCServerAdminStateRequest)
})
_sym_db.RegisterMessage(ListOfNiCServerAdminStateRequest)

ListOfNiCServerAdminStateReply = _reflection.GeneratedProtocolMessageType('ListOfNiCServerAdminStateReply', (_message.Message,), {                              # noqa: E501
    'DESCRIPTOR': _LISTOFNICSERVERADMINSTATEREPLY,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfNiCServerAdminStateReply)
})
_sym_db.RegisterMessage(ListOfNiCServerAdminStateReply)

ListOfFlapCounterRequest = _reflection.GeneratedProtocolMessageType('ListOfFlapCounterRequest', (_message.Message,), {
    'DESCRIPTOR': _LISTOFFLAPCOUNTERREQUEST,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfFlapCounterRequest)
})
_sym_db.RegisterMessage(ListOfFlapCounterRequest)

ListOfFlapCounterReply = _reflection.GeneratedProtocolMessageType('ListOfFlapCounterReply', (_message.Message,), {
    'DESCRIPTOR': _LISTOFFLAPCOUNTERREPLY,
    '__module__': 'nic_simulator_grpc_mgmt_service_pb2'
    # @@protoc_insertion_point(class_scope:ListOfFlapCounterReply)
})
_sym_db.RegisterMessage(ListOfFlapCounterReply)

_DUALTORMGMTSERVICE = DESCRIPTOR.services_by_name['DualTorMgmtService']
if _descriptor._USE_C_DESCRIPTORS == False:                                 # noqa: E712

    DESCRIPTOR._options = None
    _LISTOFADMINREQUEST._serialized_start = 75
    _LISTOFADMINREQUEST._serialized_end = 157
    _LISTOFADMINREPLY._serialized_start = 159
    _LISTOFADMINREPLY._serialized_end = 236
    _LISTOFOPERATIONREQUEST._serialized_start = 238
    _LISTOFOPERATIONREQUEST._serialized_end = 332
    _LISTOFOPERATIONREPLY._serialized_start = 334
    _LISTOFOPERATIONREPLY._serialized_end = 423
    _LISTOFDROPREQUEST._serialized_start = 425
    _LISTOFDROPREQUEST._serialized_end = 504
    _LISTOFDROPREPLY._serialized_start = 506
    _LISTOFDROPREPLY._serialized_end = 580
    _LISTOFNICSERVERADMINSTATEREQUEST._serialized_start = 582
    _LISTOFNICSERVERADMINSTATEREQUEST._serialized_end = 661
    _LISTOFNICSERVERADMINSTATEREPLY._serialized_start = 663
    _LISTOFNICSERVERADMINSTATEREPLY._serialized_end = 759
    _LISTOFFLAPCOUNTERREQUEST._serialized_start = 761
    _LISTOFFLAPCOUNTERREQUEST._serialized_end = 862
    _LISTOFFLAPCOUNTERREPLY._serialized_start = 864
    _LISTOFFLAPCOUNTERREPLY._serialized_end = 960
    _DUALTORMGMTSERVICE._serialized_start = 963
    _DUALTORMGMTSERVICE._serialized_end = 1503
# @@protoc_insertion_point(module_scope)
