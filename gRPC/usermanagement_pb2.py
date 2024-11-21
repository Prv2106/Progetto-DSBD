# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: usermanagement.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'usermanagement.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14usermanagement.proto\x12\x0eusermanagement\"4\n\x13UserRegisterRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x0e\n\x06ticker\x18\x02 \x01(\t\"\x1f\n\x0eUserIdentifier\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"F\n\x12StockValueResponse\x12\x0e\n\x06ticker\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x02\x12\x11\n\ttimestamp\x18\x03 \x01(\t\"0\n\x0cUserResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t2\xb6\x01\n\x0bUserService\x12Q\n\x0cRegisterUser\x12#.usermanagement.UserRegisterRequest\x1a\x1c.usermanagement.UserResponse\x12T\n\x0eGetLatestValue\x12\x1e.usermanagement.UserIdentifier\x1a\".usermanagement.StockValueResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'usermanagement_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_USERREGISTERREQUEST']._serialized_start=40
  _globals['_USERREGISTERREQUEST']._serialized_end=92
  _globals['_USERIDENTIFIER']._serialized_start=94
  _globals['_USERIDENTIFIER']._serialized_end=125
  _globals['_STOCKVALUERESPONSE']._serialized_start=127
  _globals['_STOCKVALUERESPONSE']._serialized_end=197
  _globals['_USERRESPONSE']._serialized_start=199
  _globals['_USERRESPONSE']._serialized_end=247
  _globals['_USERSERVICE']._serialized_start=250
  _globals['_USERSERVICE']._serialized_end=432
# @@protoc_insertion_point(module_scope)
