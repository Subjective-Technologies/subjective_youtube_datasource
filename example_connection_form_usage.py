#!/usr/bin/env python3
"""
Example Usage of SubjectiveYouTubeDataSource Enhanced Connection Form

This script demonstrates how to use the comprehensive connection form
that covers all available YouTube processing features.
"""

from SubjectiveYouTubeDataSource import SubjectiveYouTubeDataSource
import json
import pprint

def main():
    print("🎥 YouTube Data Source Connection Form Demo")
    print("=" * 50)
    
    # Initialize the data source
    config = {
        'whisper_model_size': 'base',
        'max_retries': 3,
        'audio_quality': '192'
    }
    
    youtube_source = SubjectiveYouTubeDataSource(config)
    
    # Get the comprehensive connection form
    connection_data = youtube_source.get_connection_data()
    
    # Display service information
    print(f"\n📋 Service Information:")
    print(f"   Name: {connection_data['service_name']}")
    print(f"   Status: {connection_data['connection_status']}")
    print(f"   Description: {connection_data['description']}")
    
    # Display available input types
    print(f"\n🔧 Available Input Types:")
    for option in connection_data['connection_form']['input_type']['options']:
        print(f"   • {option['label']} ({option['value']})")
    
    # Display available processing modes
    print(f"\n⚙️  Available Processing Modes:")
    for option in connection_data['connection_form']['processing_mode']['options']:
        print(f"   • {option['label']}")
        print(f"     Script: {option['script']}")
    
    # Display capabilities
    print(f"\n🚀 Service Capabilities:")
    for capability, value in connection_data['capabilities'].items():
        print(f"   • {capability}: {value}")
    
    # Show script and dependency status
    print(f"\n📄 Script Availability:")
    scripts_available = connection_data['status']['scripts_available']
    available_count = sum(scripts_available.values())
    total_count = len(scripts_available)
    print(f"   Available: {available_count}/{total_count} scripts")
    
    print(f"\n📦 Dependencies Status:")
    deps_status = connection_data['status']['dependencies_status']
    deps_available = sum(deps_status.values())
    total_deps = len(deps_status)
    print(f"   Available: {deps_available}/{total_deps} dependencies")
    
    # Demonstrate different usage scenarios
    print(f"\n" + "=" * 50)
    print("🧪 Testing Different Usage Scenarios")
    print("=" * 50)
    
    # Scenario 1: Single URL with custom class processing
    print(f"\n1️⃣  Single URL - Custom Class Processing")
    form_data_1 = {
        'input_type': 'single_url',
        'processing_mode': 'custom_class',
        'input_data': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'whisper_model': 'base',
        'output_options': {
            'output_format': 'json',
            'include_metadata': True
        }
    }
    
    result_1 = youtube_source.process_connection_form_data(form_data_1)
    print(f"   Result: {'✅ Success' if result_1['success'] else '❌ Failed'}")
    if result_1['success']:
        print(f"   Script: {result_1['script_used']}")
        print(f"   Info: {result_1['output_info']}")
    
    # Scenario 2: Single URL with external script
    print(f"\n2️⃣  Single URL - External Script (Audio Only)")
    form_data_2 = {
        'input_type': 'single_url',
        'processing_mode': 'audio_only',
        'input_data': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'advanced_options': {
            'audio_quality': '192',
            'max_retries': 3
        }
    }
    
    result_2 = youtube_source.process_connection_form_data(form_data_2)
    print(f"   Result: {'✅ Success' if result_2['success'] else '❌ Failed'}")
    if result_2['success']:
        print(f"   Script: {result_2['script_used']}")
        print(f"   Note: {result_2.get('note', 'N/A')}")
    
    # Scenario 3: Batch processing
    print(f"\n3️⃣  Batch Processing - URL List File")
    form_data_3 = {
        'input_type': 'url_list_file',
        'processing_mode': 'context_generation',
        'input_data': 'youtube_urls.txt',  # Would need to exist
        'batch_options': {
            'batch_size': 5,
            'start_index': 0,
            'interactive_mode': True,
            'continue_on_error': True
        },
        'output_options': {
            'clean_urls_first': True,
            'convert_live_urls': True
        }
    }
    
    result_3 = youtube_source.process_connection_form_data(form_data_3)
    print(f"   Result: {'✅ Success' if result_3['success'] else '❌ Failed'}")
    if not result_3['success']:
        print(f"   Error: {result_3['error']}")
    
    # Scenario 4: Search query processing
    print(f"\n4️⃣  Search Query Processing")
    form_data_4 = {
        'input_type': 'search_query',
        'processing_mode': 'search_summary',
        'input_data': 'machine learning tutorials',
        'search_options': {
            'max_results': 10
        }
    }
    
    result_4 = youtube_source.process_connection_form_data(form_data_4)
    print(f"   Result: {'✅ Success' if result_4['success'] else '❌ Failed'}")
    if result_4['success']:
        print(f"   Script: {result_4['script_used']}")
        print(f"   Query: {result_4['input_data']}")
    
    # Show features mapping for different input types
    print(f"\n" + "=" * 50)
    print("🗺️  Features Mapping by Input Type")
    print("=" * 50)
    
    for input_type, modes in connection_data['features_mapping'].items():
        print(f"\n📝 {input_type.replace('_', ' ').title()}:")
        for mode, details in modes.items():
            print(f"   • {mode}: {details['script']}")
            print(f"     Output: {details['output']}")
    
    # Show utility scripts
    print(f"\n🔧 Utility Scripts:")
    for script, description in connection_data['utility_scripts'].items():
        print(f"   • {script}: {description}")
    
    # Cleanup
    youtube_source.cleanup()
    
    print(f"\n" + "=" * 50)
    print("✅ Demo completed successfully!")
    print("💡 Use this connection form structure to integrate with your UI/application")
    print("=" * 50)

def display_form_structure():
    """Display the complete form structure for developers."""
    
    youtube_source = SubjectiveYouTubeDataSource()
    connection_data = youtube_source.get_connection_data()
    
    print("📋 Complete Connection Form Structure:")
    print("=" * 50)
    
    # Pretty print the form structure
    form_structure = connection_data['connection_form']
    pprint.pprint(form_structure, width=80, depth=4)
    
    youtube_source.cleanup()

if __name__ == "__main__":
    try:
        main()
        
        print(f"\n\n" + "=" * 50)
        print("📋 Want to see the complete form structure?")
        response = input("Display form structure? (y/n): ").lower().strip()
        
        if response == 'y':
            print(f"\n")
            display_form_structure()
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc() 