import json
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Union, Optional

from . import api
from ._types import MessageTypes, ChannelPrivacyTypes, EventTypes
from .channel import PublicTextChannel, PrivateChannel, Channel
from .context import Context
from .gateway import Requestable
from .guild import Guild
from .interface import LazyLoadable
from .user import User, GuildUser


class RawMessage(ABC):
    """
    Basic and common features of kinds of messages.

    now support Message kinds:
        1. Message (sent by users, those normal chats such as TEXT/IMG etc.)
        2. Event (sent by system, such as notifications and broadcasts)
    """

    _type: int
    _channel_type: str
    target_id: str
    author_id: str
    content: str
    _msg_id: str
    msg_timestamp: int
    nonce: str
    extra: Any

    def __init__(self, **kwargs):
        self._msg_id = kwargs.get('msg_id')
        self._type = kwargs.get('type')
        self._channel_type = kwargs.get('channel_type')
        self.target_id = kwargs.get('target_id')
        self.author_id = kwargs.get('author_id')
        self.content = kwargs.get('content')
        self.msg_timestamp = kwargs.get('msg_timestamp')
        self.nonce = kwargs.get('nonce')
        self.extra = kwargs.get('extra', {})

    @property
    def id(self) -> str:
        """message's id"""
        return self._msg_id

    @property
    def type(self) -> MessageTypes:
        """message's type, refer to MessageTypes for enum detail"""
        return MessageTypes(self._type)

    @property
    def channel_type(self) -> ChannelPrivacyTypes:
        """type of the channel where the message in"""
        return ChannelPrivacyTypes(self._channel_type)


class Message(RawMessage, Requestable, LazyLoadable, ABC):
    """
    Represents the messages sent by user.

    Because it has source and context, we can interact with its sender and context via it.

    now there are two types of message:
        1. ChannelMessage: sent in a guild channel
        2. PrivateMessage: sent in a private chat
    """
    # QuotedMessage fields
    _ctx: Context
    _id: str
    _type: int
    content: str
    author: User  # init in subclass, override in `PublicMessage`
    # Message fields but not in QuotedMessage
    embeds: List[Dict[str, Union[str, int]]]
    attachments: Optional[Dict[str, Union[str, int, float]]]
    reactions: List[Dict[str, Union[int, bool, Dict[str, str]]]]
    quote: Optional['Message']  # init and override type in subclass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._id = kwargs.get('rong_id', kwargs.get('msg_id', kwargs.get('id')))
        self._type = kwargs.get('type')
        self.content = kwargs.get('content')
        self.gate = kwargs.get('_gate_')

    @property
    def id(self) -> str:
        """quote message's id"""
        return self._id

    @property
    def type(self) -> MessageTypes:
        """quote message's type, refer to MessageTypes for enum detail"""
        return MessageTypes(self._type)

    @property
    def ctx(self) -> Context:
        """message context: channel, guild etc."""
        return self._ctx

    @property
    @abstractmethod
    def channel(self) -> Channel:
        """the channel where the message in"""
        raise NotImplementedError

    @abstractmethod
    async def add_reaction(self, emoji: str):
        """add emoji to msg's reaction list
        https://developer.kaiheila.cn/doc/http/message#%E7%BB%99%E6%9F%90%E4%B8%AA%E6%B6%88%E6%81%AF%E6%B7%BB%E5%8A%A0%E5%9B%9E%E5%BA%94
        https://developer.kaiheila.cn/doc/http/direct-message#%E7%BB%99%E6%9F%90%E4%B8%AA%E6%B6%88%E6%81%AF%E6%B7%BB%E5%8A%A0%E5%9B%9E%E5%BA%94
        :param emoji: 😘
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_reaction(self, emoji: str, user: User):
        """delete emoji from msg's reaction list
        https://developer.kaiheila.cn/doc/http/message#%E5%88%A0%E9%99%A4%E6%B6%88%E6%81%AF%E7%9A%84%E6%9F%90%E4%B8%AA%E5%9B%9E%E5%BA%94
        https://developer.kaiheila.cn/doc/http/direct-message#%E5%88%A0%E9%99%A4%E6%B6%88%E6%81%AF%E7%9A%84%E6%9F%90%E4%B8%AA%E5%9B%9E%E5%BA%94
        :param emoji: 😘
        :param user: whose reaction, delete others added reaction requires channel msg admin permission
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, content: Union[str, List], *, quote: str = None, temp_target_id: str = None):
        """Update the message content, the type of content should be same the original type of the message
        https://developer.kookapp.cn/doc/http/message#%E6%9B%B4%E6%96%B0%E9%A2%91%E9%81%93%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        https://developer.kookapp.cn/doc/http/direct-message#%E6%9B%B4%E6%96%B0%E7%A7%81%E4%BF%A1%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        :param content: updated content, its type should be same as the original type
        :param quote: the id of the message that will be quoted
        :param temp_target_id: only update the message for which user (PublicChannel)
        """
        raise NotImplementedError

    @abstractmethod
    async def reply(
            self, content: Union[str, List], use_quote: bool = True, is_temp: bool = False, *,
            type: MessageTypes = None, nonce: str = None, **kwargs
    ):
        """
        reply to a msg, content can also be a card
        https://developer.kookapp.cn/doc/http/message#%E5%8F%91%E9%80%81%E9%A2%91%E9%81%93%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        https://developer.kookapp.cn/doc/http/direct-message#%E5%8F%91%E9%80%81%E7%A7%81%E4%BF%A1%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        :param content: reply content
        :param use_quote: reply message quotes to this message.
        :param is_temp: only show the message for which user (PublicChannel)
        :param type: message type
        :param nonce: random str and returns the same.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self):
        """
        delete the message, permission required
        https://developer.kookapp.cn/doc/http/message#%E5%88%A0%E9%99%A4%E9%A2%91%E9%81%93%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        https://developer.kookapp.cn/doc/http/direct-message#%E5%88%A0%E9%99%A4%E7%A7%81%E4%BF%A1%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF
        """
        raise NotImplementedError


class PublicMessage(Message):
    """
    Messages sent in a `PublicTextChannel`
    """
    author: GuildUser
    # Not in Quote Message:
    # the message mentioned(also call as at/tagged) users' id
    mention: List[str]
    # if the message mentioned(also call as at/tagged) all
    mention_all: bool
    # the message mentioned(also call as at/tagged) roles' id
    mention_roles: List[int]
    # if the message mentioned(also call as at/tagged) all online users in the channel
    mention_here: bool
    mention_part: List[Dict[str, str]]
    mention_role_part: List[Dict[str, Union[str, int, list]]]
    channel_part: List[Dict[str, str]]
    quote: Optional['PublicMessage']

    def __init__(self, **kwargs):
        """
        :param _gate_: gate
        """
        super().__init__(**kwargs)
        self._update_fields(**kwargs)
        self._loaded = kwargs.get('_lazy_loaded_', False)

    def _update_fields(self, **kwargs):
        extra = kwargs.get('extra', {})
        from_event = (len(extra) != 0)
        self._ctx = Context(
            channel=PublicTextChannel(
                id=kwargs.get('target_id') if from_event else kwargs.get('channel_id'),
                name=extra.get('channel_name') if from_event else None,
                _gate_=self.gate
            ),
            guild=Guild(id=extra['guild_id'], _gate_=self.gate) if from_event else None,
            _lazy_loaded_=from_event,
        )
        if from_event:
            self.author = GuildUser(guild_id=extra['guild_id'], **extra['author'])
            self.mention = extra['mention']
            self.mention_all = extra['mention_all']
            self.mention_roles = extra['mention_roles']
            self.mention_here = extra['mention_here']
            self.mention_part = extra['kmarkdown']['mention_part']
            self.mention_role_part = extra['kmarkdown']['mention_role_part']
            self.channel_part = extra['kmarkdown']['channel_part']
            if extra.get('quote') is not None:
                self.quote = PublicMessage(**extra['quote'], _gate_=self.gate)
            else:
                self.quote = None
        else:
            self.author = GuildUser(**kwargs.get('author', {}))
            self.mention = kwargs.get('mention')
            self.mention_all = kwargs.get('mention_all')
            self.mention_roles = kwargs.get('mention_roles')
            self.mention_here = kwargs.get('mention_here')
            mention_info = kwargs.get('mention_info', kwargs.get('kmarkdown', {
                'mention_part': [], 'mention_role_part': [], 'channel_part': []
            }))
            self.mention_part = mention_info.get('mention_part')
            self.mention_role_part = mention_info.get('mention_role_part')
            self.channel_part = mention_info.get('channel_part')

            if kwargs.get('quote') is not None:
                self.quote = PublicMessage(**kwargs.get('quote'), _gate_=self.gate)
            else:
                self.quote = None
            self.embeds = kwargs.get('embeds')
            self.attachments = kwargs.get('attachments')
            self.reactions = kwargs.get('reactions')
            self._channel_type = ChannelPrivacyTypes.PERSON.name

    async def load(self):
        req = api.Message.view(msg_id=self.id)
        self._update_fields(**(await self.gate.exec_req(req)))
        if isinstance(self._ctx.channel, PublicTextChannel):
            if self._ctx.channel.guild_id is None:
                await self._ctx.channel.load()
            self._ctx.guild = Guild(id=self._ctx.channel.guild_id, _gate_=self.gate)
            self.author.guild_id = self._ctx.channel.guild_id
        self._loaded = True

    @property
    def guild(self) -> Guild:
        """the guild where the message in"""
        return self.ctx.guild

    @property
    def channel(self) -> PublicTextChannel:
        """the channel where the message in"""
        if isinstance(self.ctx.channel, PublicTextChannel):
            return self.ctx.channel
        raise ValueError('PublicMessage should be placed in PublicTextChannel')

    async def add_reaction(self, emoji: str):
        req = api.Message.addReaction(msg_id=self.id, emoji=emoji)
        return await self.gate.exec_req(req)

    async def delete_reaction(self, emoji: str, user: User):
        req = api.Message.deleteReaction(msg_id=self.id, emoji=emoji, user_id=user.id if user else '')
        return await self.gate.exec_req(req)

    async def update(self, content: Union[str, List], *, quote: str = None, temp_target_id: str = None):
        if isinstance(content, List):
            content = json.dumps(content)
        params = {'msg_id': self.id, 'content': content}
        if quote is not None:
            params['quote'] = quote
        if temp_target_id is not None:
            params['temp_target_id'] = temp_target_id
        return await self.gate.exec_req(api.Message.update(**params))

    async def reply(
            self, content: Union[str, List], use_quote: bool = True, is_temp: bool = False, *,
            type: MessageTypes = None, nonce: str = None, **kwargs
    ):
        if use_quote:
            kwargs['quote'] = self.id
        if is_temp:
            kwargs['temp_target_id'] = self.author.id
        return await self.ctx.channel.send(content, type=type, nonce=nonce, **kwargs)

    async def delete(self):
        req = api.Message.delete(msg_id=self.id)
        return await self.gate.exec_req(req)


class PrivateMessage(Message):
    """
    Messages sent in a `PrivateChannel`
    """
    author: User
    quote: Optional['PrivateMessage']
    # in QuotedMessage
    read_status: bool

    def __init__(self, **kwargs):
        """
        :param _gate_: gate
        :param code: chat code if not from event
        """
        super().__init__(**kwargs)
        self._update_fields(**kwargs)
        self._loaded = kwargs.get('_lazy_loaded_', False)

    def _update_fields(self, **kwargs):
        extra = kwargs.get('extra', {})
        from_event = (len(extra) != 0)
        self.author = User(
            **(extra['author'] if from_event else {'id': kwargs.get('author_id')}),
            _gate_=self.gate,
            _lazy_loaded_=not from_event,
        )
        self._ctx = Context(
            channel=PrivateChannel(
                id=extra['code'] if from_event else kwargs.get('code'),
                target_info=self.author,
                _gate_=self.gate
            ),
            guild=None,
            _lazy_loaded_=False,
        )

        if from_event:
            self.quote = (
                PrivateMessage(**extra.get('quote'), _gate_=self.gate)
                if extra.get('quote') is not None else
                None
            )
        else:
            self.quote = (
                PrivateMessage(**kwargs.get('quote'), _gate_=self.gate)
                if kwargs.get('quote') is not None else
                None
            )
            self.read_status = kwargs.get('read_status')
            self.embeds = kwargs.get('embeds')
            # WHY `attachments` may get `False`, `None` and `{...: ...}`???
            self.attachments = None if kwargs.get('attachments') is False else kwargs.get('attachments')
            self.reactions = kwargs.get('reactions')
            self._channel_type = ChannelPrivacyTypes.PERSON.name

    async def load(self):
        req = api.DirectMessage.view(chat_code=self.ctx.channel.id, msg_id=self.id)
        self._update_fields(**(await self.gate.exec_req(req)))
        self._loaded = True

    @property
    def chat_code(self) -> str:
        """the chat code of this private chat"""
        return self._ctx.channel.id

    @property
    def channel(self) -> PrivateChannel:
        """the message's channel"""
        if isinstance(self.ctx.channel, PrivateChannel):
            return self.ctx.channel
        raise ValueError('PublicMessage should be placed in PublicTextChannel')

    async def add_reaction(self, emoji: str):
        req = api.DirectMessage.addReaction(msg_id=self.id, emoji=emoji)
        return await self.gate.exec_req(req)

    async def delete_reaction(self, emoji: str, user: User = None):
        req = api.DirectMessage.deleteReaction(msg_id=self.id, emoji=emoji, user_id=user.id if user is not None else '')
        return await self.gate.exec_req(req)

    async def update(self, content: Union[str, List], *, quote: str = None, _: str = None):
        if isinstance(content, List):
            content = json.dumps(content)
        params = {'msg_id': self.id, 'content': content}
        if quote is not None:
            params['quote'] = quote
        return await self.gate.exec_req(api.DirectMessage.update(**params))

    async def reply(
            self, content: Union[str, List], use_quote: bool = True, _: bool = False, *,
            type: MessageTypes = None, nonce: str = None, **kwargs
    ):
        if use_quote:
            kwargs['quote'] = self.id
        return await self.ctx.channel.send(content, type=type, nonce=nonce, **kwargs)

    async def delete(self):
        req = api.DirectMessage.delete()
        return await self.gate.exec_req(req)


class Event(RawMessage):
    """sent by system, opposites to Message, carries various types of payload"""

    @property
    def event_type(self) -> EventTypes:
        """type of the event, refer to EventTypes for enum detail"""
        return EventTypes(self.extra['type'])

    @property
    def body(self) -> Dict:
        """event body, a dict, refer to official docs with the event_type for the actual struct

        docs: https://developer.kaiheila.cn/doc/event/event-introduction"""
        return self.extra['body']
