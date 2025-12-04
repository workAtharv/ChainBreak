# ChainBreak React Frontend

A modern, high-performance React-based frontend for the ChainBreak blockchain analysis tool. This frontend provides an intuitive interface for visualizing Bitcoin transaction networks, running community detection algorithms, and managing blockchain data.

## Features

- 🚀 **High-Performance Graph Rendering**: Uses Sigma.js for efficient graph visualization
- 🎨 **Modern UI/UX**: Built with Tailwind CSS and Framer Motion for smooth animations
- 📊 **Real-time Logging**: Comprehensive logging system with filtering and export capabilities
- 🔍 **Community Detection**: Louvain algorithm integration for network analysis
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🎯 **Error Handling**: Robust error handling with user-friendly error messages
- 🔄 **Auto-fallback**: Gracefully handles backend mode changes (Neo4j/JSON)

## Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library for React
- **Sigma.js** - Graph visualization library
- **Graphology** - Graph data structure library
- **Axios** - HTTP client for API communication
- **React Hot Toast** - Toast notifications
- **Lucide React** - Beautiful icon library

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- ChainBreak backend running on port 5001

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── GraphRenderer.js    # Main graph visualization
│   │   ├── Header.js           # Application header
│   │   ├── Sidebar.js          # Control panel
│   │   └── LogViewer.js        # Log management
│   ├── utils/              # Utility functions
│   │   ├── api.js              # API communication
│   │   └── logger.js           # Logging system
│   ├── App.js              # Main application component
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
└── README.md               # This file
```

## Key Components

### GraphRenderer
The core component responsible for rendering blockchain transaction graphs using Sigma.js. Features include:
- Efficient data processing and optimization
- ForceAtlas2 layout algorithm
- Interactive node selection
- Performance monitoring and logging

### Sidebar
Control panel for managing graphs and running algorithms:
- Bitcoin address input and validation
- Transaction limit configuration
- Graph file management
- Louvain algorithm execution

### LogViewer
Comprehensive logging interface with:
- Real-time log streaming
- Level-based filtering (DEBUG, INFO, WARN, ERROR, CRITICAL)
- Search functionality
- Export capabilities
- Auto-scroll option

## API Integration

The frontend communicates with the ChainBreak backend through a comprehensive API layer:

- **Graph Management**: Fetch, save, and load transaction graphs
- **Analysis**: Run blockchain analysis and community detection
- **System Status**: Monitor backend health and mode
- **Error Handling**: Graceful fallback for API failures

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:5001
```

### Tailwind CSS

The project uses Tailwind CSS with custom color schemes and animations. Configuration can be found in `tailwind.config.js`.

## Performance Features

- **Lazy Loading**: Graph libraries are loaded on-demand
- **Efficient Rendering**: Optimized graph data processing
- **Memory Management**: Proper cleanup of Sigma.js instances
- **Debounced Updates**: Prevents excessive re-renders

## Error Handling

The application implements comprehensive error handling:

- **API Failures**: Graceful degradation with user feedback
- **Graph Errors**: Fallback UI for rendering failures
- **Network Issues**: Offline detection and retry mechanisms
- **User Input Validation**: Real-time validation with helpful messages

## Logging System

The frontend includes a sophisticated logging system:

- **Multiple Levels**: DEBUG, INFO, WARN, ERROR, CRITICAL
- **Performance Tracking**: Operation timing and metrics
- **Graph Operations**: Specialized logging for graph operations
- **Export Functionality**: Download logs for debugging

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Code Style

- Use functional components with hooks
- Implement proper error boundaries
- Follow React best practices
- Use TypeScript-like prop validation

### Testing

```bash
npm test
```

### Linting

```bash
npm run lint
```

## Troubleshooting

### Common Issues

1. **Graph Not Rendering**
   - Check browser console for errors
   - Verify backend is running
   - Ensure graph data format is correct

2. **Performance Issues**
   - Reduce transaction limit for large graphs
   - Check browser memory usage
   - Use browser dev tools for profiling

3. **API Connection Errors**
   - Verify backend URL in configuration
   - Check CORS settings
   - Ensure network connectivity

### Debug Mode

Enable debug logging by setting the log level:

```javascript
logger.setLevel('DEBUG');
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the logs using the LogViewer
- Open an issue on the repository
- Contact the development team

## Roadmap

- [ ] Advanced graph filtering
- [ ] Multiple layout algorithms
- [ ] Graph comparison tools
- [ ] Export to various formats
- [ ] Real-time data streaming
- [ ] Mobile app version
