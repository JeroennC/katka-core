from uuid import UUID

import pytest
from katka import models
from katka.constants import STATUS_INACTIVE


@pytest.mark.django_db
class TestSCMRepositoryViewSetUnauthenticated:
    """
    When a user is not logged in, no group information is available, so nothing is returned.

    For listing, that would be an empty list for other operations, an error like the object could
    not be found, except on create (you need to be part of a group and anonymous users do not have any)
    """

    def test_list(self, client, scm_repository):
        response = client.get('/scm-repositories/')
        assert response.status_code == 200
        parsed = response.json()
        assert len(parsed) == 0

    def test_get(self, client, scm_repository):
        response = client.get(f'/scm-repositories/{scm_repository.public_identifier}/')
        assert response.status_code == 404

    def test_delete(self, client, scm_repository):
        response = client.delete(f'/scm-repositories/{scm_repository.public_identifier}/')
        assert response.status_code == 404

    def test_update(self, client, credential, scm_service, scm_repository):
        url = f'/scm-repositories/{scm_repository.public_identifier}/'
        data = {'organisation': 'orgA', 'repository_name': 'repoA',
                'credential': credential.public_identifier,
                'scm_service': scm_service.public_identifier}
        response = client.put(url, data, content_type='application/json')
        assert response.status_code == 404

    def test_partial_update(self, client, scm_repository):
        url = f'/scm-repositories/{scm_repository.public_identifier}/'
        data = {'organisation': 'orgB'}
        response = client.patch(url, data, content_type='application/json')
        assert response.status_code == 404

    def test_create(self, client, credential, scm_service, scm_repository):
        url = f'/scm-repositories/'
        data = {'organisation': 'orgC', 'repository_name': 'repoC',
                'credential': credential.public_identifier,
                'scm_service': scm_service.public_identifier}
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 403


@pytest.mark.django_db
class TestSCMRepositoryViewSet:

    def test_list(self, client, logged_in_user, credential, scm_service, scm_repository):
        response = client.get('/scm-repositories/')
        assert response.status_code == 200
        parsed = response.json()
        assert len(parsed) == 1
        assert parsed[0]['organisation'] == 'acme'
        assert parsed[0]['repository_name'] == 'sample'
        assert UUID(parsed[0]['credential']) == credential.public_identifier
        assert UUID(parsed[0]['scm_service']) == scm_service.public_identifier
        UUID(parsed[0]['public_identifier'])  # should not raise

    def test_list_excludes_inactive(self, client, logged_in_user, deactivated_scm_repository):
        response = client.get('/scm-repositories/')
        assert response.status_code == 200
        parsed = response.json()
        assert len(parsed) == 0

    def test_get(self, client, logged_in_user, credential, scm_service, scm_repository):
        response = client.get(f'/scm-repositories/{scm_repository.public_identifier}/')
        assert response.status_code == 200
        parsed = response.json()
        assert parsed['organisation'] == 'acme'
        assert parsed['repository_name'] == 'sample'
        assert UUID(parsed['credential']) == credential.public_identifier
        assert UUID(parsed['scm_service']) == scm_service.public_identifier

    def test_get_excludes_inactive(self, client, logged_in_user, deactivated_scm_repository):
        response = client.get(f'/scm-repositories/{deactivated_scm_repository.public_identifier}/')
        assert response.status_code == 404

    def test_delete(self, client, logged_in_user, scm_repository):
        response = client.delete(f'/scm-repositories/{scm_repository.public_identifier}/')
        assert response.status_code == 204
        p = models.SCMRepository.objects.get(pk=scm_repository.public_identifier)
        assert p.status == STATUS_INACTIVE

    def test_update(self, client, logged_in_user, credential, scm_service, scm_repository):
        url = f'/scm-repositories/{scm_repository.public_identifier}/'
        data = {'organisation': 'orgA', 'repository_name': 'repoA',
                'credential': credential.public_identifier,
                'scm_service': scm_service.public_identifier}
        response = client.put(url, data, content_type='application/json')
        assert response.status_code == 200
        p = models.SCMRepository.objects.get(pk=scm_repository.public_identifier)
        assert p.organisation == 'orgA'

    def test_partial_update(self, client, logged_in_user, scm_repository):
        url = f'/scm-repositories/{scm_repository.public_identifier}/'
        data = {'organisation': 'orgB'}
        response = client.patch(url, data, content_type='application/json')
        assert response.status_code == 200
        p = models.SCMRepository.objects.get(pk=scm_repository.public_identifier)
        assert p.organisation == 'orgB'

    def test_create(self, client, logged_in_user, credential, scm_service):
        initial_count = models.SCMRepository.objects.count()
        url = f'/scm-repositories/'
        data = {'organisation': 'orgC', 'repository_name': 'repoC',
                'credential': credential.public_identifier,
                'scm_service': scm_service.public_identifier}
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 201
        assert models.SCMRepository.objects.filter(organisation='orgC').exists()
        assert models.SCMRepository.objects.count() == initial_count + 1
