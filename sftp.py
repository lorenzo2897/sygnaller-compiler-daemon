import subprocess


def put_file(local, remote):
    try:
        p = subprocess.run([
            'scp',
            '-i',
            '/home/ubuntu/.ssh/id_rsa',
            '-o',
            'ProxyCommand=ssh -W %h:%p -i /home/ubuntu/.ssh/id_rsa -o "StrictHostKeyChecking no" ls2715@shell3.doc.ic.ac.uk',
            '-o',
            'StrictHostKeyChecking no',
            '-r',
            local,
            'ls2715@ee-mill2.ee.ic.ac.uk:%s' % remote
        ], timeout=20, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise RuntimeError("The upload command timed out")

    if p.returncode == 1:
        raise RuntimeError("Could not upload file to Vivado servers")


def get_file(remote, local):
    try:
        p = subprocess.run([
            'scp',
            '-i',
            '/home/ubuntu/.ssh/id_rsa',
            '-o',
            'ProxyCommand=ssh -W %h:%p -i /home/ubuntu/.ssh/id_rsa -o "StrictHostKeyChecking no" ls2715@shell3.doc.ic.ac.uk',
            '-o',
            'StrictHostKeyChecking no',
            'ls2715@ee-mill2.ee.ic.ac.uk:%s' % remote,
            local
        ], timeout=30, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise RuntimeError("The upload command timed out")

    if p.returncode == 1:
        raise RuntimeError("Could not download file from Vivado servers")


# *****************************************
# Unit tests
# *****************************************

import unittest


class TestSftp(unittest.TestCase):

    def test_put_get(self):
        with open('/tmp/test_put.txt', 'w') as f:
            f.write("hello!")
        put_file('/tmp/test_put.txt', '/tmp/r_test.txt')
        get_file('/tmp/r_test.txt', '/tmp/test_get.txt')
        with open('/tmp/test_get.txt') as f:
            self.assertEqual(f.read(), "hello!")

    def test_put_error(self):
        with self.assertRaises(RuntimeError):
            put_file('/tmp/__not_exist', '/tmp/not_exist_test.txt')

    def test_get_error(self):
        with self.assertRaises(RuntimeError):
            get_file('/tmp/__not_exist', '/tmp/not_exist_test.txt')


if __name__ == '__main__':
    unittest.main()
