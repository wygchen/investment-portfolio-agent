#!/usr/bin/env python3
"""
Test script for the LangGraph workflow implementation
"""

import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the main workflow function
from backend.selection.equity_selection_agent.equity_selection_agent import run_agent_workflow, load_configuration, setup_logging

def test_workflow():
    """Test the LangGraph workflow with minimal configuration"""
    
    try:
        # Create a simple mock config
        from src.config import Config
        config = Config()
        
        # Set up logging
        setup_logging(config)
        
        logger = logging.getLogger(__name__)
        logger.info("Testing LangGraph workflow...")
        
        # Run the workflow with minimal parameters
        results = run_agent_workflow(
            regions=['US'],  # Limit to US for faster testing
            sectors=None,    # All sectors
            enable_qualitative=False,  # Disable for faster testing
            force_refresh=False,  # Use cached data
            config=config
        )
        
        if results['success']:
            logger.info("✅ Workflow completed successfully!")
            logger.info(f"Execution time: {results['execution_time']:.2f} seconds")
            logger.info(f"Initial universe: {results['initial_universe_size']} stocks")
            logger.info(f"Final selections: {results['final_selection_count']} stocks")
            
            if results['file_paths']:
                logger.info("Generated files:")
                for file_type, path in results['file_paths'].items():
                    logger.info(f"  {file_type}: {path}")
        else:
            logger.error("❌ Workflow failed!")
            logger.error(f"Error: {results.get('error', 'Unknown error')}")
            
        return results['success']
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_workflow()
    sys.exit(0 if success else 1)