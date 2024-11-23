# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import usermanagement_pb2 as usermanagement__pb2

GRPC_GENERATED_VERSION = '1.68.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in usermanagement_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class UserServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterUser = channel.unary_unary(
                '/usermanagement.UserService/RegisterUser',
                request_serializer=usermanagement__pb2.UserRegisterRequest.SerializeToString,
                response_deserializer=usermanagement__pb2.UserResponse.FromString,
                _registered_method=True)
        self.UpdateUser = channel.unary_unary(
                '/usermanagement.UserService/UpdateUser',
                request_serializer=usermanagement__pb2.UserUpdateRequest.SerializeToString,
                response_deserializer=usermanagement__pb2.UserResponse.FromString,
                _registered_method=True)
        self.DeleteUser = channel.unary_unary(
                '/usermanagement.UserService/DeleteUser',
                request_serializer=usermanagement__pb2.UserIdentifier.SerializeToString,
                response_deserializer=usermanagement__pb2.UserResponse.FromString,
                _registered_method=True)
        self.LoginUser = channel.unary_unary(
                '/usermanagement.UserService/LoginUser',
                request_serializer=usermanagement__pb2.UserIdentifier.SerializeToString,
                response_deserializer=usermanagement__pb2.UserResponse.FromString,
                _registered_method=True)
        self.GetLatestValue = channel.unary_unary(
                '/usermanagement.UserService/GetLatestValue',
                request_serializer=usermanagement__pb2.UserIdentifier.SerializeToString,
                response_deserializer=usermanagement__pb2.StockValueResponse.FromString,
                _registered_method=True)
        self.GetAverageValue = channel.unary_unary(
                '/usermanagement.UserService/GetAverageValue',
                request_serializer=usermanagement__pb2.AverageRequest.SerializeToString,
                response_deserializer=usermanagement__pb2.AverageResponse.FromString,
                _registered_method=True)


class UserServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RegisterUser(self, request, context):
        """Metodi per la gestione degli utenti
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def LoginUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetLatestValue(self, request, context):
        """Metodi per il recupero dei dati
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAverageValue(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_UserServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterUser': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterUser,
                    request_deserializer=usermanagement__pb2.UserRegisterRequest.FromString,
                    response_serializer=usermanagement__pb2.UserResponse.SerializeToString,
            ),
            'UpdateUser': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateUser,
                    request_deserializer=usermanagement__pb2.UserUpdateRequest.FromString,
                    response_serializer=usermanagement__pb2.UserResponse.SerializeToString,
            ),
            'DeleteUser': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteUser,
                    request_deserializer=usermanagement__pb2.UserIdentifier.FromString,
                    response_serializer=usermanagement__pb2.UserResponse.SerializeToString,
            ),
            'LoginUser': grpc.unary_unary_rpc_method_handler(
                    servicer.LoginUser,
                    request_deserializer=usermanagement__pb2.UserIdentifier.FromString,
                    response_serializer=usermanagement__pb2.UserResponse.SerializeToString,
            ),
            'GetLatestValue': grpc.unary_unary_rpc_method_handler(
                    servicer.GetLatestValue,
                    request_deserializer=usermanagement__pb2.UserIdentifier.FromString,
                    response_serializer=usermanagement__pb2.StockValueResponse.SerializeToString,
            ),
            'GetAverageValue': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAverageValue,
                    request_deserializer=usermanagement__pb2.AverageRequest.FromString,
                    response_serializer=usermanagement__pb2.AverageResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'usermanagement.UserService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('usermanagement.UserService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class UserService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RegisterUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/usermanagement.UserService/RegisterUser',
            usermanagement__pb2.UserRegisterRequest.SerializeToString,
            usermanagement__pb2.UserResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpdateUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/usermanagement.UserService/UpdateUser',
            usermanagement__pb2.UserUpdateRequest.SerializeToString,
            usermanagement__pb2.UserResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DeleteUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/usermanagement.UserService/DeleteUser',
            usermanagement__pb2.UserIdentifier.SerializeToString,
            usermanagement__pb2.UserResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def LoginUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/usermanagement.UserService/LoginUser',
            usermanagement__pb2.UserIdentifier.SerializeToString,
            usermanagement__pb2.UserResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetLatestValue(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/usermanagement.UserService/GetLatestValue',
            usermanagement__pb2.UserIdentifier.SerializeToString,
            usermanagement__pb2.StockValueResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetAverageValue(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/usermanagement.UserService/GetAverageValue',
            usermanagement__pb2.AverageRequest.SerializeToString,
            usermanagement__pb2.AverageResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
