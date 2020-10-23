"""Test calls to main() with different command line options."""

import time
from subprocess import CalledProcessError

import pytest

from sphinxcontrib.versioning.git import IS_WINDOWS


def test_sub_page_and_tag(tmpdir, local_docs, urls):
    """Test with sub pages and one git tag. Testing from local git repo.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    local_docs.ensure('subdir', 'sub.rst').write(
        '.. _sub:\n'
        '\n'
        'Sub\n'
        '===\n'
        '\n'
        'Sub directory sub page documentation.\n'
    )
    local_docs.join('contents.rst').write('    subdir/sub\n', mode='a')
    pytest.run(local_docs, ['git', 'add', 'subdir', 'contents.rst'])
    pytest.run(local_docs, ['git', 'commit', '-m', 'Adding subdir docs.'])
    pytest.run(local_docs, ['git', 'tag', 'v1.0.0'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)])
    assert 'Traceback' not in output

    # Check root.
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>'
    ])
    urls(destination.join('subdir', 'sub.html'), [
        '<li><a href="../master/subdir/sub.html">master</a></li>',
        '<li><a href="../v1.0.0/subdir/sub.html">v1.0.0</a></li>',
    ])

    # Check master.
    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
    ])
    urls(destination.join('master', 'subdir', 'sub.html'), [
        '<li><a href="sub.html">master</a></li>',
        '<li><a href="../../v1.0.0/subdir/sub.html">v1.0.0</a></li>',
    ])

    # Check v1.0.0.
    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'subdir', 'sub.html'), [
        '<li><a href="../../master/subdir/sub.html">master</a></li>',
        '<li><a href="sub.html">v1.0.0</a></li>',
    ])


def test_moved_docs(tmpdir, local_docs, urls):
    """Test with docs being in their own directory.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    pytest.run(local_docs, ['git', 'tag', 'v1.0.0'])  # Ignored since we only specify 'docs' in the command below.
    local_docs.ensure_dir('docs')
    pytest.run(local_docs, ['git', 'mv', 'conf.py', 'docs/conf.py'])
    pytest.run(local_docs, ['git', 'mv', 'contents.rst', 'docs/contents.rst'])
    pytest.run(local_docs, ['git', 'commit', '-m', 'Moved docs.'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0'])

    # Run.
    destination = tmpdir.join('destination')
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', 'docs', str(destination)])
    assert 'Traceback' not in output

    # Check master.
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])


def test_moved_docs_many(tmpdir, local_docs, urls):
    """Test with additional sources. Testing with --chdir. Non-created destination.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    pytest.run(local_docs, ['git', 'tag', 'v1.0.0'])
    local_docs.ensure_dir('docs')
    pytest.run(local_docs, ['git', 'mv', 'conf.py', 'docs/conf.py'])
    pytest.run(local_docs, ['git', 'mv', 'contents.rst', 'docs/contents.rst'])
    pytest.run(local_docs, ['git', 'commit', '-m', 'Moved docs.'])
    pytest.run(local_docs, ['git', 'tag', 'v1.0.1'])
    local_docs.ensure_dir('docs2')
    pytest.run(local_docs, ['git', 'mv', 'docs/conf.py', 'docs2/conf.py'])
    pytest.run(local_docs, ['git', 'mv', 'docs/contents.rst', 'docs2/contents.rst'])
    pytest.run(local_docs, ['git', 'commit', '-m', 'Moved docs again.'])
    pytest.run(local_docs, ['git', 'tag', 'v1.0.2'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0', 'v1.0.1', 'v1.0.2'])

    # Run.
    dest = tmpdir.join('destination')
    output = pytest.run(tmpdir, ['sphinx-versioning', '-c', str(local_docs), 'build', 'docs', 'docs2', '.', str(dest)])
    assert 'Traceback' not in output

    # Check root.
    urls(dest.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="v1.0.2/contents.html">v1.0.2</a></li>',
    ])

    # Check master, v1.0.0, v1.0.1, v1.0.2.
    urls(dest.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>',
    ])
    urls(dest.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>',
    ])
    urls(dest.join('v1.0.1', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v1.0.1</a></li>',
        '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>',
    ])
    urls(dest.join('v1.0.2', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="contents.html">v1.0.2</a></li>',
    ])


def test_version_change(tmpdir, local_docs, urls):
    """Verify new links are added and old links are removed when only changing versions. Using the same doc files.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    destination = tmpdir.join('destination')

    # Only master.
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', 'docs', str(destination)])
    assert 'Traceback' not in output
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])

    # Add tags.
    pytest.run(local_docs, ['git', 'tag', 'v1.0.0'])
    pytest.run(local_docs, ['git', 'tag', 'v2.0.0'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'v1.0.0', 'v2.0.0'])
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', 'docs', str(destination)])
    assert 'Traceback' not in output
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    urls(destination.join('v2.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v2.0.0</a></li>',
    ])

    # Remove one tag.
    pytest.run(local_docs, ['git', 'push', 'origin', '--delete', 'v2.0.0'])
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', 'docs', str(destination)])
    assert 'Traceback' not in output
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
    ])

    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
    ])

    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
    ])


@pytest.mark.usefixtures('local_docs')
def test_multiple_local_repos(tmpdir, urls):
    """Test from another git repo as the current working directory.

    :param tmpdir: pytest fixture.
    :param urls: conftest fixture.
    """
    other = tmpdir.ensure_dir('other')
    pytest.run(other, ['git', 'init'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    output = pytest.run(other, ['sphinx-versioning', '-c', '../local', '-v', 'build', '.', str(destination)])
    assert 'Traceback' not in output

    # Check.
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])


@pytest.mark.parametrize('no_tags', [False, True])
def test_root_ref(tmpdir, local_docs, no_tags):
    """Test --root-ref and friends.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param bool no_tags: Don't push tags. Test fallback handling.
    """
    local_docs.join('conf.py').write(
        'templates_path = ["_templates"]\n'
        'html_sidebars = {"**": ["custom.html"]}\n'
    )
    local_docs.ensure('_templates', 'custom.html').write(
        '<h3>Custom Sidebar</h3>\n'
        '<ul>\n'
        '<li>Current version: {{ current_version }}</li>\n'
        '</ul>\n'
    )
    pytest.run(local_docs, ['git', 'add', 'conf.py', '_templates'])
    pytest.run(local_docs, ['git', 'commit', '-m', 'Displaying version.'])
    time.sleep(1.5)
    if not no_tags:
        pytest.run(local_docs, ['git', 'tag', 'v2.0.0'])
        time.sleep(1.5)
        pytest.run(local_docs, ['git', 'tag', 'v1.0.0'])
    pytest.run(local_docs, ['git', 'checkout', '-b', 'f2'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'master', 'f2'] + ([] if no_tags else ['v1.0.0', 'v2.0.0']))

    for arg, expected in (('--root-ref=f2', 'f2'), ('--greatest-tag', 'v2.0.0'), ('--recent-tag', 'v1.0.0')):
        # Run.
        dest = tmpdir.join('destination', arg[2:])
        output = pytest.run(tmpdir, ['sphinx-versioning', '-N', '-c', str(local_docs), 'build', '.', str(dest), arg])
        assert 'Traceback' not in output
        # Check root.
        contents = dest.join('contents.html').read()
        if no_tags and expected != 'f2':
            expected = 'master'
        assert 'Current version: {}'.format(expected) in contents
        # Check warning.
        if no_tags and 'tag' in arg:
            assert 'No git tags with docs found in remote. Falling back to --root-ref value.' in output
        else:
            assert 'No git tags with docs found in remote. Falling back to --root-ref value.' not in output
        # Check output.
        assert 'Root ref is: {}'.format(expected) in output


@pytest.mark.parametrize('parallel', [False, True])
def test_add_remove_docs(tmpdir, local_docs, urls, parallel):
    """Test URLs to other versions of current page with docs that are added/removed between versions.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    :param bool parallel: Run sphinx-build with -j option.
    """
    if parallel and IS_WINDOWS:
        return pytest.skip('Sphinx parallel feature not available on Windows.')
    pytest.run(local_docs, ['git', 'tag', 'v1.0.0'])

    # Move once.
    local_docs.ensure_dir('sub')
    pytest.run(local_docs, ['git', 'mv', 'two.rst', 'too.rst'])
    pytest.run(local_docs, ['git', 'mv', 'three.rst', 'sub/three.rst'])
    local_docs.join('contents.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
        '\n'
        '.. toctree::\n'
        '    one\n'
        '    too\n'
        '    sub/three\n'
    )
    local_docs.join('too.rst').write(
        '.. _too:\n'
        '\n'
        'Too\n'
        '===\n'
        '\n'
        'Sub page documentation 2 too.\n'
    )
    pytest.run(local_docs, ['git', 'commit', '-am', 'Moved.'])
    pytest.run(local_docs, ['git', 'tag', 'v1.1.0'])
    pytest.run(local_docs, ['git', 'tag', 'v1.1.1'])

    # Delete.
    pytest.run(local_docs, ['git', 'rm', 'too.rst', 'sub/three.rst'])
    local_docs.join('contents.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
        '\n'
        '.. toctree::\n'
        '    one\n'
    )
    pytest.run(local_docs, ['git', 'commit', '-am', 'Deleted.'])
    pytest.run(local_docs, ['git', 'tag', 'v2.0.0'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'v1.0.0', 'v1.1.0', 'v1.1.1', 'v2.0.0', 'master'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    overflow = ['--', '-j', '2'] if parallel else []
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)] + overflow)
    assert 'Traceback' not in output

    # Check parallel.
    if parallel:
        assert 'waiting for workers' in output
    else:
        assert 'waiting for workers' not in output

    # Check root.
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('one.html'), [
        '<li><a href="master/one.html">master</a></li>',
        '<li><a href="v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="v2.0.0/one.html">v2.0.0</a></li>',
    ])

    # Check master.
    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('master', 'one.html'), [
        '<li><a href="one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])

    # Check v2.0.0.
    urls(destination.join('v2.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v2.0.0', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="one.html">v2.0.0</a></li>',
    ])

    # Check v1.1.1.
    urls(destination.join('v1.1.1', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.1', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.1', 'too.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/too.html">v1.1.0</a></li>',
        '<li><a href="too.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.1', 'sub', 'three.html'), [
        '<li><a href="../../master/contents.html">master</a></li>',
        '<li><a href="../../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../../v1.1.0/sub/three.html">v1.1.0</a></li>',
        '<li><a href="three.html">v1.1.1</a></li>',
        '<li><a href="../../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    # Check v1.1.0.
    urls(destination.join('v1.1.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.0', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.0', 'too.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="too.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/too.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.0', 'sub', 'three.html'), [
        '<li><a href="../../master/contents.html">master</a></li>',
        '<li><a href="../../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="three.html">v1.1.0</a></li>',
        '<li><a href="../../v1.1.1/sub/three.html">v1.1.1</a></li>',
        '<li><a href="../../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    # Check v1.0.0.
    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'two.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="two.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'three.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="three.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])


@pytest.mark.parametrize('verbosity', [0, 1, 3])
def test_passing_verbose(local_docs, urls, verbosity):
    """Test setting sphinx-build verbosity.

    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    :param int verbosity: Number of -v to use.
    """
    command = ['sphinx-versioning'] + (['-v'] * verbosity) + ['build', '.', 'destination']

    # Run.
    output = pytest.run(local_docs, command)
    assert 'Traceback' not in output

    # Check master.
    destination = local_docs.join('destination')
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])

    # Check output.
    if verbosity == 0:
        assert 'INFO     sphinxcontrib.versioning.__main__' not in output
        assert 'docnames to write:' not in output
    elif verbosity == 1:
        assert 'INFO     sphinxcontrib.versioning.__main__' in output
        assert 'docnames to write:' not in output
    else:
        assert 'INFO     sphinxcontrib.versioning.__main__' in output
        assert 'docnames to write:' in output


def test_whitelisting(local_docs, urls):
    """Test whitelist features.

    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    pytest.run(local_docs, ['git', 'tag', 'v1.0'])
    pytest.run(local_docs, ['git', 'tag', 'v1.0-dev'])
    pytest.run(local_docs, ['git', 'checkout', '-b', 'included', 'master'])
    pytest.run(local_docs, ['git', 'checkout', '-b', 'ignored', 'master'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'v1.0', 'v1.0-dev', 'included', 'ignored'])

    command = [
        'sphinx-versioning', '-N', 'build', '.', 'html', '-w', 'master', '-w', 'included', '-W', '^v[0-9]+.[0-9]+$'
    ]

    # Run.
    output = pytest.run(local_docs, command)
    assert 'Traceback' not in output

    # Check output.
    assert 'With docs: ignored included master v1.0 v1.0-dev' in output
    assert 'Passed whitelisting: included master v1.0' in output

    # Check root.
    urls(local_docs.join('html', 'contents.html'), [
        '<li><a href="included/contents.html">included</a></li>',
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0/contents.html">v1.0</a></li>',
    ])


@pytest.mark.parametrize('disable_banner', [False, True])
def test_banner(banner, local_docs, disable_banner):
    """Test the banner.

    :param banner: conftest fixture.
    :param local_docs: conftest fixture.
    :param bool disable_banner: Cause banner to be disabled.
    """
    pytest.run(local_docs, ['git', 'tag', 'snapshot-01'])
    local_docs.join('conf.py').write('project = "MyProject"\n', mode='a')
    pytest.run(local_docs, ['git', 'commit', '-am', 'Setting project name.'])
    pytest.run(local_docs, ['git', 'checkout', '-b', 'stable', 'master'])
    pytest.run(local_docs, ['git', 'checkout', 'master'])
    local_docs.join('conf.py').write('author = "me"\n', mode='a')
    pytest.run(local_docs, ['git', 'commit', '-am', 'Setting author name.'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'master', 'stable', 'snapshot-01'])

    # Run.
    destination = local_docs.ensure_dir('..', 'destination')
    args = ['--show-banner', '--banner-main-ref', 'unknown' if disable_banner else 'stable']
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)] + args)
    assert 'Traceback' not in output

    # Handle no banner.
    if disable_banner:
        assert 'Disabling banner.' in output
        assert 'Banner main ref is' not in output
        banner(destination.join('contents.html'), None)
        return
    assert 'Disabling banner.' not in output
    assert 'Banner main ref is: stable' in output

    # Check banner.
    banner(destination.join('stable', 'contents.html'), None)  # No banner in main ref.
    for subdir in (False, True):
        banner(
            destination.join('master' if subdir else '', 'contents.html'),
            '{}stable/contents.html'.format('../' if subdir else ''),
            'the development version of MyProject. The main version is stable',
        )
    banner(destination.join('snapshot-01', 'contents.html'), '../stable/contents.html',
           'an old version of Python. The main version is stable')


def test_banner_css_override(banner, local_docs):
    """Test the banner CSS being present even if user overrides html_context['css_files'].

    :param banner: conftest fixture.
    :param local_docs: conftest fixture.
    """
    local_docs.join('conf.py').write("html_context = {'css_files': ['_static/theme_overrides.css']}\n", mode='a')
    local_docs.join('conf.py').write("html_static_path = ['_static']\n", mode='a')
    pytest.run(local_docs, ['git', 'commit', '-am', 'Setting override.'])
    pytest.run(local_docs, ['git', 'checkout', '-b', 'other', 'master'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'master', 'other'])

    # Run.
    destination = local_docs.ensure_dir('..', 'destination')
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', str(destination), '--show-banner'])
    assert 'Traceback' not in output
    assert 'Disabling banner.' not in output
    assert 'Banner main ref is: master' in output

    # Check banner.
    banner(destination.join('master', 'contents.html'), None)  # No banner in main ref.
    banner(destination.join('other', 'contents.html'), '../master/contents.html',
           'the development version of Python. The main version is master')

    # Check CSS.
    contents = destination.join('other', 'contents.html').read()
    assert 'rel="stylesheet" href="_static/banner.css"' in contents
    assert destination.join('other', '_static', 'banner.css').check(file=True)


def test_error_bad_path(tmpdir):
    """Test handling of bad paths.

    :param tmpdir: pytest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(tmpdir, ['sphinx-versioning', '-N', '-c', 'unknown', 'build', '.', str(tmpdir)])
    assert 'Directory "unknown" does not exist.' in exc.value.output

    tmpdir.ensure('is_file')
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(tmpdir, ['sphinx-versioning', '-N', '-c', 'is_file', 'build', '.', str(tmpdir)])
    assert 'Directory "is_file" is a file.' in exc.value.output

    with pytest.raises(CalledProcessError) as exc:
        pytest.run(tmpdir, ['sphinx-versioning', '-N', 'build', '.', str(tmpdir)])
    assert 'Failed to find local git repository root in {}.'.format(repr(str(tmpdir))) in exc.value.output

    repo = tmpdir.ensure_dir('repo')
    pytest.run(repo, ['git', 'init'])
    empty = tmpdir.ensure_dir('empty1857')
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(repo, ['sphinx-versioning', '-N', '-g', str(empty), 'build', '.', str(tmpdir)])
    assert 'Failed to find local git repository root in' in exc.value.output
    assert 'empty1857' in exc.value.output


def test_error_no_docs_found(tmpdir, local):
    """Test no docs to build.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(local, ['sphinx-versioning', '-N', '-v', 'build', '.', str(tmpdir)])
    assert 'No docs found in any remote branch/tag. Nothing to do.' in exc.value.output


def test_error_bad_root_ref(tmpdir, local_docs):
    """Test bad root ref.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(local_docs, ['sphinx-versioning', '-N', '-v', 'build', '.', str(tmpdir), '-r', 'unknown'])
    assert 'Root ref unknown not found in: master' in exc.value.output


def test_bad_banner(banner, local_docs):
    """Test bad banner main ref.

    :param banner: conftest fixture.
    :param local_docs: conftest fixture.
    """
    pytest.run(local_docs, ['git', 'checkout', '-b', 'stable', 'master'])
    local_docs.join('conf.py').write('bad\n', mode='a')
    pytest.run(local_docs, ['git', 'commit', '-am', 'Breaking stable.'])
    pytest.run(local_docs, ['git', 'push', 'origin', 'stable'])

    # Run.
    destination = local_docs.ensure_dir('..', 'destination')
    args = ['--show-banner', '--banner-main-ref', 'stable']
    output = pytest.run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)] + args)
    assert 'KeyError' not in output

    # Check no banner.
    assert 'Banner main ref is: stable' in output
    assert 'Banner main ref stable failed during pre-run.' in output
    banner(destination.join('contents.html'), None)
