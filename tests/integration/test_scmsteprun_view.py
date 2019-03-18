from uuid import UUID

import pytest
from katka import models
from katka.constants import STEP_STATUS_INPROGRESS, STEP_STATUS_SUCCESS


@pytest.mark.django_db
class TestSCMStepRunViewSetUnauthenticated:
    """
    When a user is not logged in, no group information is available, so nothing is returned.

    For listing, that would be an empty list for other operations, an error like the object could
    not be found, except on create (you need to be part of a group and anonymous users do not have any)
    """

    def test_list(self, client, scm_step_run):
        response = client.get('/scm-step-runs/')
        assert response.status_code == 200
        parsed = response.json()
        assert len(parsed) == 0

    def test_get(self, client, scm_step_run):
        response = client.get(f'/scm-step-runs/{scm_step_run.public_identifier}/')
        assert response.status_code == 404

    def test_delete(self, client, scm_step_run):
        response = client.delete(f'/scm-step-runs/{scm_step_run.public_identifier}/')
        assert response.status_code == 404

    def test_update(self, client, scm_pipeline_run, scm_step_run):
        url = f'/scm-step-runs/{scm_step_run.public_identifier}/'
        data = {'slug': 'release',
                'name': 'Release product',
                'stage': 'Production',
                'status': STEP_STATUS_SUCCESS,
                'output': 'Command completed',
                'scm_pipeline_run': scm_pipeline_run.public_identifier}
        response = client.put(url, data, content_type='application/json')
        assert response.status_code == 404

    def test_partial_update(self, client, scm_step_run):
        url = f'/scm-step-runs/{scm_step_run.public_identifier}/'
        data = {'output': 'Step executed.'}
        response = client.patch(url, data, content_type='application/json')
        assert response.status_code == 404

    def test_create(self, client, scm_pipeline_run, scm_step_run):
        url = f'/scm-step-runs/'
        data = {'slug': 'release',
                'name': 'Release product',
                'stage': 'Production',
                'status': STEP_STATUS_INPROGRESS,
                'scm_pipeline_run': scm_pipeline_run.public_identifier}
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 403


@pytest.mark.django_db
class TestSCMStepRunViewSet:

    def test_list(self, client, logged_in_user, scm_pipeline_run, scm_step_run):
        response = client.get('/scm-step-runs/')
        assert response.status_code == 200
        parsed = response.json()
        assert len(parsed) == 1
        assert parsed[0]['slug'] == 'release'
        assert parsed[0]['name'] == 'Release Katka'
        assert parsed[0]['stage'] == 'Production'
        assert parsed[0]['status'] == STEP_STATUS_INPROGRESS
        assert parsed[0]['output'] == ''
        assert UUID(parsed[0]['scm_pipeline_run']) == scm_pipeline_run.public_identifier
        UUID(parsed[0]['public_identifier'])  # should not raise

    def test_list_excludes_inactive(self, client, logged_in_user, deactivated_scm_step_run):
        response = client.get('/scm-step-runs/')
        assert response.status_code == 200
        parsed = response.json()
        assert len(parsed) == 0

    def test_get(self, client, logged_in_user, scm_pipeline_run, scm_step_run):
        response = client.get(f'/scm-step-runs/{scm_step_run.public_identifier}/')
        assert response.status_code == 200
        parsed = response.json()
        assert parsed['slug'] == 'release'
        assert parsed['name'] == 'Release Katka'
        assert parsed['stage'] == 'Production'
        assert parsed['status'] == STEP_STATUS_INPROGRESS
        assert parsed['output'] == ''
        assert UUID(parsed['scm_pipeline_run']) == scm_pipeline_run.public_identifier
        UUID(parsed['public_identifier'])  # should not raise

    def test_get_excludes_inactive(self, client, logged_in_user, deactivated_scm_step_run):
        response = client.get(f'/scm-step-runs/{deactivated_scm_step_run.public_identifier}/')
        assert response.status_code == 404

    def test_delete(self, client, logged_in_user, scm_step_run):
        response = client.delete(f'/scm-step-runs/{scm_step_run.public_identifier}/')
        assert response.status_code == 204
        p = models.SCMStepRun.objects.get(pk=scm_step_run.public_identifier)
        assert p.deleted is True

    def test_update(self, client, logged_in_user, scm_pipeline_run, scm_step_run):
        url = f'/scm-step-runs/{scm_step_run.public_identifier}/'
        data = {'slug': 'release',
                'name': 'Release product',
                'stage': 'Production',
                'status': STEP_STATUS_SUCCESS,
                'output': 'Command completed',
                'scm_pipeline_run': scm_pipeline_run.public_identifier}
        response = client.put(url, data, content_type='application/json')
        assert response.status_code == 200
        p = models.SCMStepRun.objects.get(pk=scm_step_run.public_identifier)
        assert p.name == 'Release product'

    def test_partial_update(self, client, logged_in_user, scm_step_run):
        url = f'/scm-step-runs/{scm_step_run.public_identifier}/'
        data = {'output': 'Step executed.'}
        response = client.patch(url, data, content_type='application/json')
        assert response.status_code == 200
        p = models.SCMStepRun.objects.get(pk=scm_step_run.public_identifier)
        assert p.output == 'Step executed.'

    def test_create(self, client, logged_in_user, scm_pipeline_run, scm_step_run):
        initial_count = models.SCMStepRun.objects.count()
        url = f'/scm-step-runs/'
        data = {'slug': 'release',
                'name': 'Release product',
                'stage': 'Production',
                'status': STEP_STATUS_INPROGRESS,
                'scm_pipeline_run': scm_pipeline_run.public_identifier}
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 201
        assert models.SCMStepRun.objects.filter(name='Release product').exists()
        assert models.SCMStepRun.objects.count() == initial_count + 1