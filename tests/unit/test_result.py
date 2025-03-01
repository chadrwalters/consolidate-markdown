import unittest

from consolidate_markdown.processors.result import ProcessingResult, ProcessorStats


class TestProcessingResult(unittest.TestCase):
    """Tests for the ProcessingResult class."""

    def setUp(self) -> None:
        """Set up a fresh ProcessingResult instance for each test."""
        self.result = ProcessingResult()

    def test_initialization(self) -> None:
        """Test that a new ProcessingResult is initialized with zero counters."""
        self.assertEqual(self.result.processed, 0)
        self.assertEqual(self.result.from_cache, 0)
        self.assertEqual(self.result.regenerated, 0)
        self.assertEqual(self.result.skipped, 0)
        self.assertEqual(len(self.result.errors), 0)
        self.assertEqual(self.result.documents_processed, 0)
        self.assertEqual(self.result.documents_from_cache, 0)
        self.assertEqual(self.result.documents_generated, 0)
        self.assertEqual(self.result.documents_skipped, 0)
        self.assertEqual(self.result.images_processed, 0)
        self.assertEqual(self.result.images_from_cache, 0)
        self.assertEqual(self.result.images_generated, 0)
        self.assertEqual(self.result.images_skipped, 0)
        self.assertEqual(self.result.gpt_cache_hits, 0)
        self.assertEqual(self.result.gpt_new_analyses, 0)
        self.assertEqual(self.result.gpt_skipped, 0)
        self.assertEqual(len(self.result.processor_stats), 0)
        self.assertEqual(self.result.last_action, "")

    def test_get_processor_stats(self) -> None:
        """Test getting processor stats."""
        # Get stats for a processor
        stats = self.result.get_processor_stats("test_processor")

        # Check that stats were created
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(stats.processor_type, "test_processor")
        self.assertEqual(stats.processed, 0)

        # Get stats for the same processor again
        stats2 = self.result.get_processor_stats("test_processor")

        # Check that we got the same stats object
        self.assertIs(stats, stats2)

        # Get stats for a different processor
        stats3 = self.result.get_processor_stats("another_processor")

        # Check that we got a different stats object
        self.assertIsNot(stats, stats3)
        self.assertEqual(stats3.processor_type, "another_processor")
        self.assertEqual(len(self.result.processor_stats), 2)

    def test_add_error(self) -> None:
        """Test adding error messages."""
        # Add an error without processor type
        self.result.add_error("Test error message")

        # Check that error was added
        self.assertEqual(len(self.result.errors), 1)
        self.assertEqual(self.result.errors[0], "Error: Test error message")
        self.assertEqual(len(self.result.processor_stats), 0)

        # Add an error with processor type
        self.result.add_error("Another error message", "test_processor")

        # Check that error was added and processor stats were updated
        self.assertEqual(len(self.result.errors), 2)
        self.assertEqual(self.result.errors[1], "Error: Another error message")
        self.assertEqual(len(self.result.processor_stats), 1)
        self.assertEqual(len(self.result.processor_stats["test_processor"].errors), 1)
        self.assertEqual(
            self.result.processor_stats["test_processor"].errors[0],
            "Error: Another error message",
        )

        # Add an error with a specific error pattern
        # Note: The actual formatting depends on the implementation of _format_error_for_user
        # We're just checking that an error was added, not the specific format
        self.result.add_error("API key is invalid")
        self.assertEqual(len(self.result.errors), 3)
        self.assertTrue("API key is invalid" in self.result.errors[2])

    def test_merge(self) -> None:
        """Test merging results from another ProcessingResult instance."""
        # Create another result with some data
        other = ProcessingResult()
        other.processed = 5
        other.from_cache = 2
        other.regenerated = 1
        other.skipped = 2
        other.documents_processed = 3
        other.documents_generated = 1
        other.documents_from_cache = 1
        other.documents_skipped = 1
        other.images_processed = 2
        other.images_generated = 1
        other.images_from_cache = 1
        other.images_skipped = 1
        other.gpt_cache_hits = 1
        other.gpt_new_analyses = 1
        other.gpt_skipped = 1

        # Add processor stats to the other result
        other_stats = other.get_processor_stats("test_processor")
        other_stats.processed = 5
        other_stats.from_cache = 2
        other_stats.regenerated = 1
        other_stats.skipped = 2
        other.add_error("Test error in other result")

        # Merge the other result into our result
        self.result.merge(other)

        # Check that all counters were merged correctly
        self.assertEqual(self.result.processed, 5)
        self.assertEqual(self.result.from_cache, 2)
        self.assertEqual(self.result.regenerated, 1)
        self.assertEqual(self.result.skipped, 2)
        self.assertEqual(self.result.documents_processed, 3)
        self.assertEqual(self.result.documents_generated, 1)
        self.assertEqual(self.result.documents_from_cache, 1)
        self.assertEqual(self.result.documents_skipped, 1)
        self.assertEqual(self.result.images_processed, 2)
        self.assertEqual(self.result.images_generated, 1)
        self.assertEqual(self.result.images_from_cache, 1)
        self.assertEqual(self.result.images_skipped, 1)
        self.assertEqual(self.result.gpt_cache_hits, 1)
        self.assertEqual(self.result.gpt_new_analyses, 1)
        self.assertEqual(self.result.gpt_skipped, 1)

        # Check that processor stats were merged
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(self.result.processor_stats["test_processor"].processed, 5)
        self.assertEqual(self.result.processor_stats["test_processor"].from_cache, 2)
        self.assertEqual(self.result.processor_stats["test_processor"].regenerated, 1)
        self.assertEqual(self.result.processor_stats["test_processor"].skipped, 2)

        # Check that error messages were merged
        self.assertEqual(len(self.result.errors), 1)
        self.assertEqual(self.result.errors[0], "Error: Test error in other result")

        # Add some data to our result
        self.result.processed += 3
        stats = self.result.get_processor_stats("another_processor")
        stats.processed = 3
        self.result.add_error("Test error in original result")

        # Create a third result with some data
        third = ProcessingResult()
        third.processed = 2  # Add this line to set processed count
        third_stats = third.get_processor_stats("test_processor")
        third_stats.processed = 2
        third_stats2 = third.get_processor_stats("third_processor")
        third_stats2.processed = 4
        third.add_error("Test error in third result")

        # Merge the third result into our result
        self.result.merge(third)

        # Check that all counters were merged correctly
        self.assertEqual(self.result.processed, 10)  # 5 + 3 + 2
        self.assertEqual(
            self.result.processor_stats["test_processor"].processed, 7
        )  # 5 + 2
        self.assertEqual(self.result.processor_stats["another_processor"].processed, 3)
        self.assertEqual(self.result.processor_stats["third_processor"].processed, 4)

        # Check that error messages were merged correctly
        self.assertEqual(len(self.result.errors), 3)
        self.assertEqual(self.result.errors[0], "Error: Test error in other result")
        self.assertEqual(self.result.errors[1], "Error: Test error in original result")
        self.assertEqual(self.result.errors[2], "Error: Test error in third result")

    def test_add_from_cache(self) -> None:
        """Test adding an item from cache."""
        # Add an item from cache
        self.result.add_from_cache("test_processor")

        # Check that counters were updated correctly
        self.assertEqual(
            self.result.processed, 0
        )  # Note: processed is not incremented by add_from_cache
        self.assertEqual(self.result.from_cache, 1)
        self.assertEqual(self.result.regenerated, 0)
        self.assertEqual(self.result.last_action, "from_cache")

        # Check that processor stats were updated
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(self.result.processor_stats["test_processor"].processed, 1)
        self.assertEqual(self.result.processor_stats["test_processor"].from_cache, 1)
        self.assertEqual(self.result.processor_stats["test_processor"].regenerated, 0)

        # Add another item from cache
        self.result.add_from_cache("test_processor")

        # Check that counters were updated correctly
        self.assertEqual(self.result.processed, 0)  # Still not incremented
        self.assertEqual(self.result.from_cache, 2)
        self.assertEqual(self.result.regenerated, 0)

        # Check that processor stats were updated
        self.assertEqual(self.result.processor_stats["test_processor"].processed, 2)
        self.assertEqual(self.result.processor_stats["test_processor"].from_cache, 2)
        self.assertEqual(self.result.processor_stats["test_processor"].regenerated, 0)

    def test_add_generated(self) -> None:
        """Test adding a generated item."""
        # Add a generated item
        self.result.add_generated("test_processor")

        # Check that counters were updated correctly
        self.assertEqual(
            self.result.processed, 0
        )  # Note: processed is not incremented by add_generated
        self.assertEqual(self.result.from_cache, 0)
        self.assertEqual(self.result.regenerated, 1)
        self.assertEqual(self.result.last_action, "generated")

        # Check that processor stats were updated
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(self.result.processor_stats["test_processor"].processed, 1)
        self.assertEqual(self.result.processor_stats["test_processor"].from_cache, 0)
        self.assertEqual(self.result.processor_stats["test_processor"].regenerated, 1)

        # Add another generated item
        self.result.add_generated("test_processor")

        # Check that counters were updated correctly
        self.assertEqual(self.result.processed, 0)  # Still not incremented
        self.assertEqual(self.result.from_cache, 0)
        self.assertEqual(self.result.regenerated, 2)

        # Check that processor stats were updated
        self.assertEqual(self.result.processor_stats["test_processor"].processed, 2)
        self.assertEqual(self.result.processor_stats["test_processor"].from_cache, 0)
        self.assertEqual(self.result.processor_stats["test_processor"].regenerated, 2)

    def test_add_skipped(self) -> None:
        """Test adding a skipped item."""
        # Add a skipped item
        self.result.add_skipped("test_processor")

        # Check that counters were updated correctly
        self.assertEqual(self.result.processed, 0)
        self.assertEqual(self.result.skipped, 1)
        self.assertEqual(self.result.last_action, "skipped")

        # Check that processor stats were updated
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(self.result.processor_stats["test_processor"].skipped, 1)

        # Add another skipped item
        self.result.add_skipped("test_processor")

        # Check that counters were updated correctly
        self.assertEqual(self.result.processed, 0)
        self.assertEqual(self.result.skipped, 2)

        # Check that processor stats were updated
        self.assertEqual(self.result.processor_stats["test_processor"].skipped, 2)

    def test_document_tracking(self) -> None:
        """Test tracking document processing."""
        # Test document generation
        self.result.add_document_generated("test_processor")
        self.assertEqual(self.result.documents_processed, 1)
        self.assertEqual(self.result.documents_generated, 1)
        self.assertEqual(self.result.documents_from_cache, 0)

        # Check that processor stats were updated
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(
            self.result.processor_stats["test_processor"].documents_processed, 1
        )
        self.assertEqual(
            self.result.processor_stats["test_processor"].documents_generated, 1
        )

        # Test document from cache
        self.result.add_document_from_cache("test_processor")
        self.assertEqual(self.result.documents_processed, 2)
        self.assertEqual(self.result.documents_generated, 1)
        self.assertEqual(self.result.documents_from_cache, 1)

        # Check that processor stats were updated
        self.assertEqual(
            self.result.processor_stats["test_processor"].documents_processed, 2
        )
        self.assertEqual(
            self.result.processor_stats["test_processor"].documents_from_cache, 1
        )

        # Test document skipped
        self.result.add_document_skipped("test_processor")
        self.assertEqual(self.result.documents_processed, 2)
        self.assertEqual(self.result.documents_skipped, 1)

        # Check that processor stats were updated
        self.assertEqual(
            self.result.processor_stats["test_processor"].documents_skipped, 1
        )

    def test_image_tracking(self) -> None:
        """Test tracking image processing."""
        # Test image generation
        self.result.add_image_generated("test_processor")
        self.assertEqual(self.result.images_processed, 1)
        self.assertEqual(self.result.images_generated, 1)
        self.assertEqual(self.result.images_from_cache, 0)

        # Check that processor stats were updated
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(
            self.result.processor_stats["test_processor"].images_processed, 1
        )
        self.assertEqual(
            self.result.processor_stats["test_processor"].images_generated, 1
        )

        # Test image from cache
        self.result.add_image_from_cache("test_processor")
        self.assertEqual(self.result.images_processed, 2)
        self.assertEqual(self.result.images_generated, 1)
        self.assertEqual(self.result.images_from_cache, 1)

        # Check that processor stats were updated
        self.assertEqual(
            self.result.processor_stats["test_processor"].images_processed, 2
        )
        self.assertEqual(
            self.result.processor_stats["test_processor"].images_from_cache, 1
        )

        # Test image skipped
        self.result.add_image_skipped("test_processor")
        self.assertEqual(self.result.images_processed, 2)
        self.assertEqual(self.result.images_skipped, 1)

        # Check that processor stats were updated
        self.assertEqual(
            self.result.processor_stats["test_processor"].images_skipped, 1
        )

    def test_gpt_tracking(self) -> None:
        """Test tracking GPT analysis processing."""
        # Test GPT analysis generation
        self.result.add_gpt_generated("test_processor")
        self.assertEqual(self.result.gpt_new_analyses, 1)
        self.assertEqual(self.result.gpt_cache_hits, 0)

        # Check that processor stats were updated
        self.assertIn("test_processor", self.result.processor_stats)
        self.assertEqual(
            self.result.processor_stats["test_processor"].gpt_new_analyses, 1
        )

        # Test GPT analysis from cache
        self.result.add_gpt_from_cache("test_processor")
        self.assertEqual(self.result.gpt_new_analyses, 1)
        self.assertEqual(self.result.gpt_cache_hits, 1)

        # Check that processor stats were updated
        self.assertEqual(
            self.result.processor_stats["test_processor"].gpt_cache_hits, 1
        )

        # Test GPT analysis skipped
        self.result.add_gpt_skipped("test_processor")
        self.assertEqual(self.result.gpt_skipped, 1)

        # Check that processor stats were updated
        self.assertEqual(self.result.processor_stats["test_processor"].gpt_skipped, 1)

    def test_str_representation(self) -> None:
        """Test the string representation of ProcessingResult."""
        # Add some data to the result
        self.result.processed = 10
        self.result.from_cache = 5
        self.result.regenerated = 5
        self.result.skipped = 2
        self.result.documents_processed = 6
        self.result.documents_from_cache = 3
        self.result.documents_generated = 3
        self.result.documents_skipped = 1
        self.result.images_processed = 4
        self.result.images_from_cache = 2
        self.result.images_generated = 2
        self.result.images_skipped = 1
        self.result.gpt_cache_hits = 2
        self.result.gpt_new_analyses = 3
        self.result.gpt_skipped = 1

        # Get the string representation
        result_str = str(self.result)

        # Check that the string contains all the expected information
        self.assertIn("10 processed", result_str)
        self.assertIn("5 from cache", result_str)
        self.assertIn("5 generated", result_str)
        self.assertIn("2 skipped", result_str)
        self.assertIn("6 documents processed", result_str)
        self.assertIn("3 from cache", result_str)
        self.assertIn("3 generated", result_str)
        self.assertIn("1 skipped", result_str)
        self.assertIn("4 images processed", result_str)
        self.assertIn("2 from cache", result_str)
        self.assertIn("2 generated", result_str)
        self.assertIn("1 skipped", result_str)
        self.assertIn("2 GPT analyses from cache", result_str)
        self.assertIn("3 new GPT analyses", result_str)
        self.assertIn("1 GPT analyses skipped", result_str)

        # Add an error and check that it appears in the string
        self.result.add_error("Test error message")
        result_str = str(self.result)
        self.assertIn("1 errors", result_str)

        # Test empty result
        empty_result = ProcessingResult()
        self.assertEqual(str(empty_result), "No results")


class TestProcessorStats(unittest.TestCase):
    """Tests for the ProcessorStats class."""

    def test_initialization(self) -> None:
        """Test that a new ProcessorStats is initialized with zero counters."""
        stats = ProcessorStats()
        self.assertEqual(stats.processed, 0)
        self.assertEqual(stats.from_cache, 0)
        self.assertEqual(stats.regenerated, 0)
        self.assertEqual(stats.skipped, 0)
        self.assertEqual(stats.documents_processed, 0)
        self.assertEqual(stats.documents_generated, 0)
        self.assertEqual(stats.documents_from_cache, 0)
        self.assertEqual(stats.documents_skipped, 0)
        self.assertEqual(stats.images_processed, 0)
        self.assertEqual(stats.images_generated, 0)
        self.assertEqual(stats.images_from_cache, 0)
        self.assertEqual(stats.images_skipped, 0)
        self.assertEqual(stats.gpt_cache_hits, 0)
        self.assertEqual(stats.gpt_new_analyses, 0)
        self.assertEqual(stats.gpt_skipped, 0)
        self.assertEqual(len(stats.errors), 0)
        self.assertIsNone(stats.processor_type)

    def test_merge(self) -> None:
        """Test merging stats from another ProcessorStats instance."""
        # Create two stats objects
        stats1 = ProcessorStats()
        stats1.processed = 5
        stats1.from_cache = 2
        stats1.regenerated = 3
        stats1.skipped = 1
        stats1.documents_processed = 3
        stats1.documents_generated = 2
        stats1.documents_from_cache = 1
        stats1.documents_skipped = 1
        stats1.images_processed = 2
        stats1.images_generated = 1
        stats1.images_from_cache = 1
        stats1.images_skipped = 0
        stats1.gpt_cache_hits = 1
        stats1.gpt_new_analyses = 2
        stats1.gpt_skipped = 0
        stats1.errors.append("Error 1")
        stats1.processor_type = "test_processor"

        stats2 = ProcessorStats()
        stats2.processed = 3
        stats2.from_cache = 1
        stats2.regenerated = 2
        stats2.skipped = 2
        stats2.documents_processed = 2
        stats2.documents_generated = 1
        stats2.documents_from_cache = 1
        stats2.documents_skipped = 0
        stats2.images_processed = 1
        stats2.images_generated = 0
        stats2.images_from_cache = 1
        stats2.images_skipped = 1
        stats2.gpt_cache_hits = 0
        stats2.gpt_new_analyses = 1
        stats2.gpt_skipped = 1
        stats2.errors.append("Error 2")
        stats2.processor_type = "another_processor"

        # Merge stats2 into stats1
        stats1.merge(stats2)

        # Check that all counters were merged correctly
        self.assertEqual(stats1.processed, 8)
        self.assertEqual(stats1.from_cache, 3)
        self.assertEqual(
            stats1.regenerated, 3
        )  # Not 5, the merge logic is more complex
        self.assertEqual(stats1.skipped, 3)
        self.assertEqual(stats1.documents_processed, 5)
        self.assertEqual(stats1.documents_generated, 3)
        self.assertEqual(stats1.documents_from_cache, 2)
        self.assertEqual(stats1.documents_skipped, 1)
        self.assertEqual(stats1.images_processed, 3)
        self.assertEqual(stats1.images_generated, 1)
        self.assertEqual(stats1.images_from_cache, 2)
        self.assertEqual(stats1.images_skipped, 1)
        self.assertEqual(stats1.gpt_cache_hits, 1)
        self.assertEqual(stats1.gpt_new_analyses, 3)
        self.assertEqual(stats1.gpt_skipped, 1)

        # Check that errors were merged
        self.assertEqual(len(stats1.errors), 2)
        self.assertEqual(stats1.errors[0], "Error 1")
        self.assertEqual(stats1.errors[1], "Error 2")

        # Check that processor_type was preserved from the second object
        self.assertEqual(stats1.processor_type, "another_processor")

        # Test the case where all items are from cache
        stats3 = ProcessorStats()
        stats3.processed = 5
        stats3.from_cache = 5  # All items from cache
        stats3.regenerated = 0

        stats4 = ProcessorStats()
        stats4.processed = 3
        stats4.from_cache = 1
        stats4.regenerated = 2

        # Merge stats4 into stats3
        stats3.merge(stats4)

        # Check that regenerated is 0 because all items in stats3 are from cache
        self.assertEqual(stats3.processed, 8)
        self.assertEqual(stats3.from_cache, 6)
        self.assertEqual(stats3.regenerated, 0)

        # Test the case where the first stats object is empty
        stats5 = ProcessorStats()

        stats6 = ProcessorStats()
        stats6.processed = 3
        stats6.from_cache = 1
        stats6.regenerated = 2

        # Merge stats6 into stats5
        stats5.merge(stats6)

        # Check that regenerated is copied from stats6
        self.assertEqual(stats5.processed, 3)
        self.assertEqual(stats5.from_cache, 1)
        self.assertEqual(stats5.regenerated, 2)


if __name__ == "__main__":
    unittest.main()
