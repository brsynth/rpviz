import pytest
from pathlib import Path
from rpviz import cli


IN_DIR = Path(__file__).resolve().parent / 'inputs' / 'as_dir'
IN_TAR = Path(__file__).resolve().parent / 'inputs' / 'as_tar.tgz'


def test_build_arg_parser(mocker):
    # No args
    args = ['prog']
    mocker.patch('sys.argv', args)
    parser = cli.__build_arg_parser()
    with pytest.raises(SystemExit):
        args = parser.parse_args()


def test_dir_input(mocker, tmpdir):
    out_dir = tmpdir / 'odir'
    args = ['prog', str(IN_DIR), str(out_dir)]
    mocker.patch('sys.argv', args)
    parser = cli.__build_arg_parser()
    args = parser.parse_args()
    cli.__run(args)


def test_tar_input(mocker, tmpdir):
    out_dir = tmpdir / 'odir'
    args = ['prog', str(IN_TAR), str(out_dir)]
    mocker.patch('sys.argv', args)
    parser = cli.__build_arg_parser()
    args = parser.parse_args()
    cli.__run(args)