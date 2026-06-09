import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  IconButton,
  Chip,
  Link,
  Alert
} from '@mui/material';
import {
  Close as CloseIcon,
  OpenInNew as OpenInNewIcon,
  Visibility as VisibilityIcon,
  Campaign as CampaignIcon
} from '@mui/icons-material';

const AdBanner = ({ 
  position = 'sidebar', // 'sidebar', 'banner', 'inline'
  maxAds = 3,
  showCloseButton = false,
  className = ''
}) => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [closedAds, setClosedAds] = useState(new Set());

  // Anúncios de exemplo para a indústria de Cannabis
  const sampleAds = [
    {
      id: 1,
      title: "Cannabis Premium - Óleos Medicinais",
      description: "Óleos de CBD e THC de alta qualidade para tratamentos terapêuticos. Certificados e testados em laboratório.",
      image: "/Oelo.png",
      url: "https://example.com/cannabis-premium",
      company: "Cannabis Premium Ltda",
      category: "Produtos",
      price: "A partir de R$ 150,00",
      highlight: "Entrega em todo Brasil",
      type: "product"
    },
    {
      id: 2,
      title: "Curso de Cannabis Medicinal",
      description: "Capacitação completa para profissionais de saúde. Certificado reconhecido pelo CFM.",
      image: "/Flor óleo.jpeg",
      url: "https://example.com/curso-cannabis",
      company: "Instituto Cannabis Brasil",
      category: "Educação",
      price: "R$ 890,00",
      highlight: "100% Online",
      type: "course"
    },
    {
      id: 3,
      title: "Laboratório de Análises Canábicas",
      description: "Análises completas de potência, pesticidas e metais pesados. Laudos técnicos certificados.",
      image: "/AraOS.png",
      url: "https://example.com/laboratorio",
      company: "CannaLab Análises",
      category: "Serviços",
      price: "Consulte preços",
      highlight: "Resultados em 48h",
      type: "service"
    },
    {
      id: 4,
      title: "Equipamentos para Cultivo",
      description: "LED grow lights, estufas, sistemas de irrigação e todos os equipamentos para cultivo medicinal.",
      image: "/AraOS.png",
      url: "https://example.com/equipamentos",
      company: "GrowTech Brasil",
      category: "Equipamentos",
      price: "Promoção 20% OFF",
      highlight: "Frete Grátis",
      type: "equipment"
    },
    {
      id: 5,
      title: "Consultoria Jurídica Cannabis",
      description: "Assessoria jurídica especializada em cannabis medicinal. Habeas corpus e licenças.",
      image: "/AraOS.png",
      url: "https://example.com/juridico",
      company: "Cannabis Legal Advocacia",
      category: "Jurídico",
      price: "Consulta gratuita",
      highlight: "Especialistas em Cannabis",
      type: "legal"
    }
  ];

  useEffect(() => {
    // Carregar anúncios da API
    const loadAds = async () => {
      try {
        setLoading(true);
        
        // Tentar carregar da API real
        const response = await fetch(`/api/anuncios?limite=${maxAds}`);
        
        if (response.ok) {
          const adsData = await response.json();
          setAds(adsData);
        } else {
          // Fallback para dados de exemplo se a API falhar
          console.warn('API de anúncios indisponível, usando dados de exemplo');
          const shuffledAds = [...sampleAds].sort(() => Math.random() - 0.5);
          setAds(shuffledAds.slice(0, maxAds));
        }
      } catch (error) {
        console.error('Erro ao carregar anúncios:', error);
        // Fallback para dados de exemplo
        const shuffledAds = [...sampleAds].sort(() => Math.random() - 0.5);
        setAds(shuffledAds.slice(0, maxAds));
      } finally {
        setLoading(false);
      }
    };

    loadAds();
  }, [maxAds]);

  const handleAdClick = (ad) => {
    // Registrar clique do anúncio
    console.log('Anúncio clicado:', ad.title);
    
    // Enviar analytics para a API
    fetch(`/api/anuncios/${ad.id}/click`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(error => {
      console.warn('Erro ao registrar clique:', error);
    });
    
    // Abrir link
    window.open(ad.url, '_blank', 'noopener,noreferrer');
  };

  const handleCloseAd = (adId) => {
    setClosedAds(prev => new Set([...prev, adId]));
  };

  const getAdTypeIcon = (type) => {
    switch (type) {
      case 'product': return '🌿';
      case 'course': return '📚';
      case 'service': return '🔬';
      case 'equipment': return '⚙️';
      case 'legal': return '⚖️';
      default: return '📢';
    }
  };

  const getAdTypeColor = (type) => {
    switch (type) {
      case 'product': return '#4caf50';
      case 'course': return '#2196f3';
      case 'service': return '#ff9800';
      case 'equipment': return '#9c27b0';
      case 'legal': return '#f44336';
      default: return '#757575';
    }
  };

  const filteredAds = ads.filter(ad => !closedAds.has(ad.id));

  if (loading) {
    return (
      <Box className={className}>
        <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Carregando anúncios...
          </Typography>
        </Paper>
      </Box>
    );
  }

  if (filteredAds.length === 0) {
    return (
      <Box className={className}>
        <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
          <CampaignIcon color="disabled" sx={{ mb: 1 }} />
          <Typography variant="body2" color="text.secondary">
            Nenhum anúncio disponível
          </Typography>
        </Paper>
      </Box>
    );
  }

  // Layout para sidebar (vertical)
  if (position === 'sidebar') {
    return (
      <Box className={className}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <CampaignIcon sx={{ mr: 1 }} color="primary" />
          Parceiros Cannabis
        </Typography>
        
        {filteredAds.map((ad) => (
          <Card 
            key={ad.id} 
            elevation={2} 
            sx={{ 
              mb: 2, 
              cursor: 'pointer',
              transition: 'transform 0.2s',
              '&:hover': { transform: 'scale(1.02)' },
              position: 'relative'
            }}
            onClick={() => handleAdClick(ad)}
          >
            {showCloseButton && (
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloseAd(ad.id);
                }}
                sx={{ position: 'absolute', top: 4, right: 4, zIndex: 1 }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            )}
            
            <CardMedia
              component="img"
              height="120"
              image={ad.image}
              alt={ad.title}
              sx={{ objectFit: 'cover' }}
            />
            
            <CardContent sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ mr: 1 }}>
                  {getAdTypeIcon(ad.type)}
                </Typography>
                <Chip 
                  label={ad.category} 
                  size="small" 
                  sx={{ 
                    backgroundColor: getAdTypeColor(ad.type),
                    color: 'white',
                    fontSize: '0.7rem'
                  }}
                />
              </Box>
              
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                {ad.title}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontSize: '0.8rem' }}>
                {ad.description.length > 80 ? `${ad.description.substring(0, 80)}...` : ad.description}
              </Typography>
              
              <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                {ad.price}
              </Typography>
              
              {ad.highlight && (
                <Chip 
                  label={ad.highlight} 
                  size="small" 
                  color="secondary" 
                  sx={{ mt: 1, fontSize: '0.7rem' }}
                />
              )}
            </CardContent>
            
            <CardActions sx={{ p: 1, pt: 0 }}>
              <Button 
                size="small" 
                endIcon={<OpenInNewIcon />}
                sx={{ fontSize: '0.7rem' }}
              >
                Ver Mais
              </Button>
            </CardActions>
          </Card>
        ))}
        
        <Alert severity="info" sx={{ mt: 2, fontSize: '0.8rem' }}>
          <Typography variant="caption">
            💡 Quer anunciar aqui? Entre em contato conosco!
          </Typography>
        </Alert>
      </Box>
    );
  }

  // Layout para banner (horizontal)
  if (position === 'banner') {
    return (
      <Box className={className} sx={{ mb: 3 }}>
        <Paper elevation={2} sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <CampaignIcon sx={{ mr: 1 }} color="primary" fontSize="small" />
            Parceiros Recomendados
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, overflowX: 'auto', pb: 1 }}>
            {filteredAds.map((ad) => (
              <Card 
                key={ad.id}
                elevation={1}
                sx={{ 
                  minWidth: 280,
                  cursor: 'pointer',
                  transition: 'transform 0.2s',
                  '&:hover': { transform: 'scale(1.02)' }
                }}
                onClick={() => handleAdClick(ad)}
              >
                <Box sx={{ display: 'flex' }}>
                  <CardMedia
                    component="img"
                    sx={{ width: 80, height: 80 }}
                    image={ad.image}
                    alt={ad.title}
                  />
                  <CardContent sx={{ flex: 1, p: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                      {ad.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      {ad.description.substring(0, 60)}...
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main', fontSize: '0.8rem' }}>
                      {ad.price}
                    </Typography>
                  </CardContent>
                </Box>
              </Card>
            ))}
          </Box>
        </Paper>
      </Box>
    );
  }

  // Layout inline (dentro do conteúdo)
  return (
    <Box className={className} sx={{ my: 2 }}>
      {filteredAds.slice(0, 1).map((ad) => (
        <Paper 
          key={ad.id}
          elevation={1} 
          sx={{ 
            p: 2, 
            backgroundColor: '#f8f9fa',
            border: '1px solid #e0e0e0',
            cursor: 'pointer',
            transition: 'transform 0.2s',
            '&:hover': { transform: 'scale(1.01)' }
          }}
          onClick={() => handleAdClick(ad)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <CampaignIcon sx={{ mr: 1 }} color="primary" fontSize="small" />
            <Typography variant="caption" color="text.secondary">
              Anúncio Patrocinado
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box
              component="img"
              src={ad.image}
              alt={ad.title}
              sx={{ width: 60, height: 60, borderRadius: 1, objectFit: 'cover' }}
            />
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                {ad.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {ad.description}
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                {ad.price}
              </Typography>
            </Box>
          </Box>
        </Paper>
      ))}
    </Box>
  );
};

export default AdBanner;
