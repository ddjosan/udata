import logging
from bson import ObjectId
from flask import current_app
from math import ceil

log = logging.getLogger(__name__)


def topic_search_for(topic, adapter, **kwargs):
    """
    Search for objects related to a topic.
    
    Args:
        topic: The Topic instance to filter by
        adapter: The search adapter class (DatasetSearch, ReuseSearch)
        **kwargs: Additional search parameters
    
    Returns:
        The search results
    """
    try:
        # Get page and page_size from kwargs or use defaults
        page = int(kwargs.get('page', 1))
        page_size = int(kwargs.get('page_size', current_app.config.get('PAGE_SIZE', 20)))
        
        # Get sort parameter
        sort = kwargs.get('sort', '-created')
        
        # Convert sort parameter to MongoDB field
        if sort.startswith('-'):
            sort_field = sort[1:]
            sort_direction = -1
        else:
            sort_field = sort
            sort_direction = 1
            
        # Map sort field to actual field in database
        sort_mapping = {
            'created': 'created_at',
            'last_modified': 'last_modified',
            'title': 'title',
            'followers': 'metrics.followers',
            'views': 'metrics.views',
            'datasets': 'metrics.datasets',
            'reuses': 'metrics.reuses',
        }
        
        mongo_sort_field = sort_mapping.get(sort_field, 'created_at')
        
        # For DatasetSearch, filter by datasets with tags related to topic
        if adapter.__name__ == 'DatasetSearch':
            # Get the model from the adapter
            model = adapter.model
            
            # Start with visible objects
            query_set = model.objects.visible()
            
            # Filter by tags related to topic
            if topic.tags:
                log.debug(f"Filtering datasets by topic tags: {topic.tags}")
                query_set = query_set.filter(tags__in=topic.tags)
            else:
                log.debug(f"Topic {topic.id} has no tags, returning empty result")
                return {'data': [], 'total': 0}
            
            # Apply featured filter if present
            if 'featured' in kwargs:
                featured_value = kwargs['featured']
                if isinstance(featured_value, str):
                    featured_value = featured_value.lower() == 'true'
                query_set = query_set.filter(featured=featured_value)
                log.debug(f"Applied featured filter: {featured_value}")
            
            # Count total before pagination
            total = query_set.count()
            log.debug(f"Total datasets after filtering by tags: {total}")
            
            # Apply sorting
            query_set = query_set.order_by(f"{'-' if sort_direction == -1 else ''}{mongo_sort_field}")
            
            # Apply pagination
            skip = (page - 1) * page_size
            query_set = query_set.skip(skip).limit(page_size)
            
            # Get the results
            results = list(query_set)
            log.debug(f"Retrieved {len(results)} datasets")
            
            # Build the response
            response = {
                'data': results,
                'page': page,
                'page_size': page_size,
                'total': total,
                'next_page': page + 1 if skip + page_size < total else None,
                'previous_page': page - 1 if page > 1 else None,
                'pages': ceil(total / page_size) if page_size else 1,
            }
            
            return response
        
        # For ReuseSearch, filter by reuse IDs
        elif adapter.__name__ == 'ReuseSearch':
            # Get the model from the adapter
            model = adapter.model
            
            # Start with visible objects
            query_set = model.objects.visible()
            
            # Filter by tags related to topic
            if topic.tags:
                log.debug(f"Filtering reuses by topic tags: {topic.tags}")
                query_set = query_set.filter(tags__in=topic.tags)
            else:
                log.debug(f"Topic {topic.id} has no tags, returning empty result")
                return {'data': [], 'total': 0}
            
            # Apply featured filter if present
            if 'featured' in kwargs:
                featured_value = kwargs['featured']
                if isinstance(featured_value, str):
                    featured_value = featured_value.lower() == 'true'
                query_set = query_set.filter(featured=featured_value)
                log.debug(f"Applied featured filter: {featured_value}")
            
            # Count total before pagination
            total = query_set.count()
            log.debug(f"Total reuses after filtering by tags: {total}")
            
            # Apply sorting
            query_set = query_set.order_by(f"{'-' if sort_direction == -1 else ''}{mongo_sort_field}")
            
            # Apply pagination
            skip = (page - 1) * page_size
            query_set = query_set.skip(skip).limit(page_size)
            
            # Get the results
            results = list(query_set)
            log.debug(f"Retrieved {len(results)} reuses")
            
            # Build the response
            response = {
                'data': results,
                'page': page,
                'page_size': page_size,
                'total': total,
                'next_page': page + 1 if skip + page_size < total else None,
                'previous_page': page - 1 if page > 1 else None,
                'pages': ceil(total / page_size) if page_size else 1,
            }
            
            return response
        
        # For any other adapter, use the default search
        from udata.search import query
        log.debug(f"Using default search for adapter {adapter.__name__}")
        return query(adapter, topic=str(topic.id), **kwargs)
    except Exception as e:
        log.exception(f"Error in topic_search_for: {str(e)}")
        raise 