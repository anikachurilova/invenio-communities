# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2020 European Union.
#
# Invenio-communitys-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Communities Service API."""

from elasticsearch_dsl import Q
from invenio_db import db
from invenio_records_resources.services.base import LinksTemplate
from invenio_records_resources.services.records import RecordService
from marshmallow.exceptions import ValidationError


class CommunityService(RecordService):
    """community Service."""

    def search_user_communities(
            self, identity, params=None, es_preference=None, **kwargs):
        """Search for records matching the querystring."""
        self.require_permission(identity, 'search_user_communities')

        # Prepare and execute the search
        params = params or {}
        search_result = self._search(
            'search',
            identity,
            params,
            es_preference,
            extra_filter=Q(
                "term",
                **{"access.owned_by.user": identity.id}
            ),
            permission_action='read',
            **kwargs).execute()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(self.config.links_user_search, context={
                "args": params
            }),
            links_item_tpl=self.links_item_tpl,
        )

    def rename(self, id_, identity, data, revision_id=None):
        """Rename a community."""
        record = self.record_cls.pid.resolve(id_)

        self.check_revision_id(record, revision_id)

        # Permissions
        self.require_permission(identity, "rename", record=record)

        if 'id' not in data:
            raise ValidationError('Missing data for required field.', 'id')

        # Run components
        for component in self.components:
            if hasattr(component, 'rename'):
                component.rename(identity, data=data, record=record)

        record.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(record)

        return self.result_item(
            self,
            identity,
            record,
            links_tpl=self.links_item_tpl,
        )