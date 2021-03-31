import khquizgen as kh

if __name__ == '__main__':
    assert len(__package__) > 0, """

    The '__main__' module does not seem to have been run in the context of a
    runnable package ... did you forget to add the '-m' flag?

    Usage: python3 -m <packagename>
    """
    print(kh.main())
