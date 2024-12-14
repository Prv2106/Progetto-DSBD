# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: usermanagement.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'usermanagement.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14usermanagement.proto\x12\x0eusermanagement\"m\n\x13UserRegisterRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x0e\n\x06ticker\x18\x03 \x01(\t\x12\x11\n\tlow_value\x18\x04 \x01(\x02\x12\x12\n\nhigh_value\x18\x05 \x01(\x02\"6\n\x11UserUpdateRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x12\n\nnew_ticker\x18\x02 \x01(\t\"3\n\x10UserLoginRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"\x1f\n\x0eUserIdentifier\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"3\n\x0e\x41verageRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x12\n\nnum_values\x18\x02 \x01(\x05\"7\n\x13LowThresholdRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x11\n\tlow_value\x18\x02 \x01(\x02\"9\n\x14HighThresholdRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x12\n\nhigh_value\x18\x02 \x01(\x02\"0\n\x0cUserResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"h\n\x12StockValueResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0e\n\x06ticker\x18\x03 \x01(\t\x12\r\n\x05value\x18\x04 \x01(\x02\x12\x11\n\ttimestamp\x18\x05 \x01(\t\"T\n\x0f\x41verageResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0e\n\x06ticker\x18\x03 \x01(\t\x12\x0f\n\x07\x61verage\x18\x04 \x01(\x02\"j\n\x0f\x44\x65tailsResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0e\n\x06ticker\x18\x02 \x01(\t\x12\x11\n\tlow_value\x18\x03 \x01(\x02\x12\x12\n\nhigh_value\x18\x04 \x01(\x02\x12\x0f\n\x07message\x18\x05 \x01(\t2\xee\x05\n\x0bUserService\x12Q\n\x0cRegisterUser\x12#.usermanagement.UserRegisterRequest\x1a\x1c.usermanagement.UserResponse\x12M\n\nUpdateUser\x12!.usermanagement.UserUpdateRequest\x1a\x1c.usermanagement.UserResponse\x12J\n\nDeleteUser\x12\x1e.usermanagement.UserIdentifier\x1a\x1c.usermanagement.UserResponse\x12K\n\tLoginUser\x12 .usermanagement.UserLoginRequest\x1a\x1c.usermanagement.UserResponse\x12U\n\x0fUpdateHighValue\x12$.usermanagement.HighThresholdRequest\x1a\x1c.usermanagement.UserResponse\x12S\n\x0eUpdateLowValue\x12#.usermanagement.LowThresholdRequest\x1a\x1c.usermanagement.UserResponse\x12T\n\x0eGetLatestValue\x12\x1e.usermanagement.UserIdentifier\x1a\".usermanagement.StockValueResponse\x12R\n\x0fGetAverageValue\x12\x1e.usermanagement.AverageRequest\x1a\x1f.usermanagement.AverageResponse\x12N\n\x0bShowDetails\x12\x1e.usermanagement.UserIdentifier\x1a\x1f.usermanagement.DetailsResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'usermanagement_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_USERREGISTERREQUEST']._serialized_start=40
  _globals['_USERREGISTERREQUEST']._serialized_end=149
  _globals['_USERUPDATEREQUEST']._serialized_start=151
  _globals['_USERUPDATEREQUEST']._serialized_end=205
  _globals['_USERLOGINREQUEST']._serialized_start=207
  _globals['_USERLOGINREQUEST']._serialized_end=258
  _globals['_USERIDENTIFIER']._serialized_start=260
  _globals['_USERIDENTIFIER']._serialized_end=291
  _globals['_AVERAGEREQUEST']._serialized_start=293
  _globals['_AVERAGEREQUEST']._serialized_end=344
  _globals['_LOWTHRESHOLDREQUEST']._serialized_start=346
  _globals['_LOWTHRESHOLDREQUEST']._serialized_end=401
  _globals['_HIGHTHRESHOLDREQUEST']._serialized_start=403
  _globals['_HIGHTHRESHOLDREQUEST']._serialized_end=460
  _globals['_USERRESPONSE']._serialized_start=462
  _globals['_USERRESPONSE']._serialized_end=510
  _globals['_STOCKVALUERESPONSE']._serialized_start=512
  _globals['_STOCKVALUERESPONSE']._serialized_end=616
  _globals['_AVERAGERESPONSE']._serialized_start=618
  _globals['_AVERAGERESPONSE']._serialized_end=702
  _globals['_DETAILSRESPONSE']._serialized_start=704
  _globals['_DETAILSRESPONSE']._serialized_end=810
  _globals['_USERSERVICE']._serialized_start=813
  _globals['_USERSERVICE']._serialized_end=1563
# @@protoc_insertion_point(module_scope)
